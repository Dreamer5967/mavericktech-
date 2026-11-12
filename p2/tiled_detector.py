"""Bounded rotated-tile inference with boxes returned in original image coordinates."""
import math


def restore_box(box, x, y, rotation, width, height):
    points=[]
    for px,py in ((box[0]+x,box[1]+y),(box[2]+x,box[3]+y)):
        if rotation==0: point=(px,py)
        elif rotation==1: point=(width-py,px)
        elif rotation==2: point=(width-px,height-py)
        elif rotation==3: point=(py,height-px)
        else: raise ValueError('Rotation must be a quarter turn.')
        points.append(point)
    return [max(0,min(width,min(p[0] for p in points))),max(0,min(height,min(p[1] for p in points))),
            max(0,min(width,max(p[0] for p in points))),max(0,min(height,max(p[1] for p in points)))]


def iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/union if union>0 else 0


def suppress_duplicates(detections,threshold=0.45):
    kept=[]
    for detection in sorted(detections,key=lambda row:row['confidence'],reverse=True):
        def duplicate(row):
            a,b=detection['xyxy_pixels'],row['xyxy_pixels']
            intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            smaller=min((a[2]-a[0])*(a[3]-a[1]),(b[2]-b[0])*(b[3]-b[1]))
            return iou(a,b)>threshold or (smaller>0 and intersection/smaller>=0.8)
        if not any(duplicate(row) for row in kept):
            kept.append(detection)
    return kept


def infer_tiled(model,bgr,config,device=0):
    import numpy as np
    height,width=bgr.shape[:2]
    detections=[]
    # Four disjoint 640px tiles, four rotations: at most 16 calls per frame.
    if (width,height)!=(1280,1280):
        raise ValueError('Rotated tiles require the bounded 1280x1280 profile.')
    for rotation in range(4):
        rotated=np.ascontiguousarray(np.rot90(bgr,rotation))
        for y in (0,640):
            for x in (0,640):
                result=model.predict(source=rotated[y:y+640,x:x+640],device=device,
                    conf=config['confidence'],imgsz=960,save=False,verbose=False)[0]
                if result.boxes is None:raise RuntimeError('Detector returned no box container.')
                for box,cls,confidence in zip(result.boxes.xyxy.detach().cpu().tolist(),
                        result.boxes.cls.detach().cpu().tolist(),result.boxes.conf.detach().cpu().tolist()):
                    if not all(math.isfinite(v) for v in list(box)+[cls,confidence]):
                        raise ValueError('Nonfinite tile detection.')
                    name=result.names[int(cls)]
                    if name not in config['vehicle_classes']:continue
                    restored=restore_box(box,x,y,rotation,width,height)
                    if restored[2]<=restored[0] or restored[3]<=restored[1]:continue
                    detections.append({'class_id':int(cls),'class_name':name,'confidence':float(confidence),
                                       'xyxy_pixels':restored})
    return suppress_duplicates(detections)
