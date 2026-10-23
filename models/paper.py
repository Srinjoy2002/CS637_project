"""Exact REP models; explicit physical/output/augmented-state separation."""
from dataclasses import dataclass
import numpy as np
from .official_definition import define_system

@dataclass
class Model:
    name: str
    miss: np.ndarray
    hit: np.ndarray
    C: np.ndarray
    Q_rep: np.ndarray
    x0: np.ndarray
    dt: float
    nplant: int
    nbuffer: int
    ncontroller: int
    ninput: int
    output_scale: float
    labels: tuple

    @property
    def Q_output(self):
        return self.Q_rep * self.output_scale

    @property
    def A(self): return self.hit[:self.nplant,:self.nplant]
    @property
    def B(self): return self.hit[:self.nplant,-self.ninput:]
    def output(self, states): return np.asarray(states)[...,:self.nplant] @ self.C.T
    def metadata(self):
        return dict(name=self.name,dt=self.dt,nplant=self.nplant,nbuffer=self.nbuffer,
                    ncontroller=self.ncontroller,ninput=self.ninput,labels=self.labels,
                    hit=self.hit.tolist(),miss=self.miss.tolist(),C=self.C.tolist(),
                    Q_rep=self.Q_rep.tolist(),Q_output=self.Q_output.tolist(),x0=self.x0.tolist(),
                    extension=self.name=='qt_zero')

def get_model(name='furuta_hold'):
    if name not in ('furuta_hold','furuta_zero','qt_nmp','qt_zero'):
        raise ValueError('Unknown model')
    miss,hit,C,Q,x0,_=define_system('qt_nmp' if name=='qt_zero' else name)
    if name=='qt_zero':
        miss[-2:,-2:]=0  # Eq. (6), Delta=0: zero DEVIATION input, not pump power.
    if name.startswith('furuta'):
        return Model(name,miss,hit,C,Q,x0,.005,3,3,0,1,1.,
                     ('pendulum angle [rad]','pendulum velocity [rad/s]','arm velocity [rad/s]'))
    return Model(name,miss,hit,C,Q,x0,.1,4,2,4,2,.25,
                 ('lower tank 1 deviation','lower tank 2 deviation','upper tank 3 deviation','upper tank 4 deviation'))
