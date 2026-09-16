num_elements = 300;
dz = 1/num_elements;

Point(1) = {-0.5, -0.5, 0, 1.0};
Point(2) = {-0.5, 0.5, 0, 1.0};
Point(3) = {0.5, 0.5, 0, 1.0};
Point(4) = {0.5, -0.5, 0, 1.0};

Line(1) = {1, 2};
Line(2) = {3, 4};
Line(3) = {4, 1};
Line(4) = {2, 3};

Curve Loop(1) = {4, 2, 3, 1};
Plane Surface(1) = {1};

Transfinite Surface {1} = {1, 2, 3, 4};
Transfinite Curve {1, 4, 2, 3} = num_elements+1 Using Progression 1;
Recombine Surface {1};

Extrude {0, 0, dz} {
  Surface{1}; Layers {1}; Recombine;
}

