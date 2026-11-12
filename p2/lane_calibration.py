"""Camera projection helpers for offline lane-region calibration."""
import math


def camera_coordinates(point, transform):
    if transform['roll']!=0:
        raise ValueError('This draft projector supports zero-roll cameras only.')
    pitch,yaw=map(math.radians,(transform['pitch'],transform['yaw']))
    cp,sp,cy,sy=math.cos(pitch),math.sin(pitch),math.cos(yaw),math.sin(yaw)
    delta=[point[i]-transform[name] for i,name in enumerate(('x','y','z'))]
    axes=((cp*cy,cp*sy,sp),(-sy,cy,0),(-sp*cy,-sp*sy,cp))
    return [sum(a*b for a,b in zip(delta,axis)) for axis in axes]


def clip(poly, coordinate, boundary, keep_greater):
    if not poly:
        return []
    result=[]
    previous=poly[-1]
    inside=lambda p:p[coordinate]>=boundary if keep_greater else p[coordinate]<=boundary
    for current in poly:
        if inside(previous)!=inside(current):
            fraction=(boundary-previous[coordinate])/(current[coordinate]-previous[coordinate])
            result.append([a+fraction*(b-a) for a,b in zip(previous,current)])
        if inside(current):
            result.append(current)
        previous=current
    return result


def project_polygon(points, transform, width, height, fov):
    poly=[camera_coordinates(point,transform) for point in points]
    poly=clip(poly,0,0.1,True)
    focal=width/(2*math.tan(math.radians(fov)/2))
    poly=[[width/2+focal*p[1]/p[0],height/2-focal*p[2]/p[0]] for p in poly]
    for coordinate,boundary,greater in ((0,0,True),(0,width-1,False),(1,0,True),(1,height-1,False)):
        poly=clip(poly,coordinate,boundary,greater)
    return [[round(x,2),round(y,2)] for x,y in poly] if len(poly)>=3 else []
