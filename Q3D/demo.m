function [Wopt] = demo(data)

yt = data(:,2);
idx = find(data(:,1) == 0);
xl = data(1:idx-1,1);
xu = data(idx:end,1);

%load airfoil
Winit = [-1 -1 -1 -1 1 1 1 1]; % initial weights

% Run the optimization code
options = optimoptions('fmincon','Display','off');
[Wopt]=fmincon(@(W) airfoilfit(W,yt,xl,xu,0),Winit,[],[],[],[],ones(1,8)*-1,ones(1,8),[], options);

% Generate the CST airfoil with optimum weights
%[ycoord] = CST_airfoil_fit(Wopt,xl,xu,0);

%plot([XL; XU], ycoord, ".")

end