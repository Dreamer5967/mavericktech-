"""Offline cost estimator. Does not access or change a Vast.ai account."""
from dataclasses import dataclass
import argparse, json, math
@dataclass(frozen=True)
class Budget:
    credit: float = 5.0
    compute_per_hour: float = 0.30
    storage_per_hour: float = 0.0
    transfer_allowance: float = 0.50
    reserve: float = 1.0
    def hours(self) -> float:
        values = (self.credit, self.compute_per_hour, self.storage_per_hour,
                  self.transfer_allowance, self.reserve)
        if any(not math.isfinite(x) or x < 0 for x in values):
            raise ValueError('All values must be finite and nonnegative.')
        rate = self.compute_per_hour + self.storage_per_hour
        if rate <= 0:
            raise ValueError('The combined hourly rate must be positive.')
        return max(0.0, (self.credit-self.transfer_allowance-self.reserve)/rate)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--credit',type=float,default=5)
    p.add_argument('--compute',type=float,required=True)
    p.add_argument('--storage',type=float,default=0)
    p.add_argument('--transfer',type=float,default=0.50)
    p.add_argument('--reserve',type=float,default=1)
    a=p.parse_args()
    try:
        b=Budget(a.credit,a.compute,a.storage,a.transfer,a.reserve)
        h=b.hours()
    except ValueError as e:p.error(str(e))
    print(json.dumps({'estimated_running_hours':round(h,3),
      'assumptions':vars(a), 'warning':'Estimate only. No auto-stop. Check actual billing; stopped storage is extra.'},indent=2))
if __name__=='__main__': main()
