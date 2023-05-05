function [Res, AC] = run_q3d(wing_planform_geom, wing_incidence_angle, visc_option,  root_data, tip_data,air_density, velocity, reynolds_number,cl)
    disp("Print root data")
    disp(root_data)

   % Wing planform geometry
   %                x    y     z   chord(m)    twist angle (deg)
%    AC.Wing.Geom = [0     0     0     3.5         0;
%                    0.9  14.5   0     1.4         0];
    AC.Wing.Geom = wing_planform_geom;

   % Wing incidence angle (degree)
%    AC.Wing.inc  = 0;
     AC.Wing.inc  = wing_incidence_angle;

    root_cst = demo(root_data)
    tip_cst  = demo(tip_data)
   % Airfoil coefficients input matrix
   %                    | ->     upper curve coeff.                <-|   | ->       lower curve coeff.       <-|
   %AC.Wing.Airfoils   = [0.2171    0.3450    0.2975    0.2685    0.2893  -0.1299   -0.2388   -0.1635   -0.0476    0.0797;
   %                      0.2171    0.3450    0.2975    0.2685    0.2893  -0.1299   -0.2388   -0.1635   -0.0476    0.0797];

   AC.Wing.Airfoils = [root_cst;
                       tip_cst];

   AC.Wing.eta = [0;1];  % Spanwise location of the airfoil sections

   % Viscous vs inviscid
   AC.Visc  = visc_option;              % 0 for inviscid and 1 for viscous analysis
   AC.Aero.MaxIterIndex = 150;    %Maximum number of Iteration for the
                                   %convergence of viscous calculation


   % Flight Condition
   AC.Aero.V     = velocity/3.6;            % flight speed (m/s)
   AC.Aero.rho   = air_density;         % air density  (kg/m3)
   AC.Aero.alt   = 0;             % flight altitude (m)
   AC.Aero.Re    = reynolds_number;        % reynolds number (bqased on mean aerodynamic chord)
   AC.Aero.M     = 0.2;           % flight Mach number
   AC.Aero.CL    = cl;          % lift coefficient - comment this line to run the code for given alpha%
   %AC.Aero.Alpha = 2;             % angle of attack -  comment this line to run the code for given cl


   %%
   tic

   Res = Q3D_solver(AC);

   toc

end