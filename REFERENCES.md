# Scientific references and independent checks

All inputs and outputs are SI. Standard gravity is the conventional 9.80665 m/s²;
it is a default, not an assertion about local gravity. Other input values in tests
are explicitly chosen hypothetical experiments, not measured material data.

Sources:
- NASA, Bernoulli's equation and its steady/incompressible/inviscid assumptions:
  https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/bernoullis-equation/
- EPA EPANET 2.2 manual, Darcy-Weisbach and regime-dependent friction:
  https://www.epa.gov/system/files/documents/2021-07/epanet_users_manual_2.2.0-1.pdf
- OpenStax University Physics, Archimedes' principle:
  https://openstax.org/books/university-physics-volume-1/pages/14-4-archimedes-principle-and-buoyancy

Reference derivations (independent of calling the implementation):
1. Q=.01 m³/s and areas .01/.005 m² yield 1/2 m/s. At equal elevation,
   ideal downstream pressure changes by 1000*(1²-2²)/2 = -1500 Pa.
   One metre of additional loss removes 1000*9.80665=9806.65 Pa.
2. A depth of 2 m at density 1000 kg/m³ gives 1000*9.80665*2=19613.3 Pa.
3. A vertical rectangle of width 1 m and height 2 m, top at free surface,
   has triangular load: F=1000*9.80665*1*2²/2=19613.3 N. Its centroid
   is 2H/3=4/3 m below the top. For only the lower 1 m wetted, F=4903.325 N
   and force position is 1+2/3=5/3 m from the original top edge.
4. For D=.1 m, L=10 m, mu=.001 Pa*s, rho=1000 and V=.01 m/s,
   Re=1000. Independently, Hagen-Poiseuille gives delta_p=32*mu*L*V/D²=.32 Pa.
5. An exact constructed Colebrook case: f=.04, x=1/sqrt(f)=5, Re=12550,
   epsilon/D=3.7*(10^(-2.5)-.001). Then epsilon/(3.7D)+2.51*x/Re=10^(-2.5),
   and -2 log10(...) = 5. This is an algebraic test, not experimental data.
6. Displacing .5 m³ at density 1000 gives 4903.325 N. A 500 kg body weighs
   4903.325 N; required displacement is .5 m³, with .25 m draft for a 2 m² prism.

The transition interval [2000,4000) is an explicit conservative teaching policy,
not a universal physical boundary. The turbulent software envelope Re<=1e8 and
relative roughness<=.05 is a scope limit, not a physical law. These implementations
are analytically tested; independent faculty/experimental validation remains pending.
