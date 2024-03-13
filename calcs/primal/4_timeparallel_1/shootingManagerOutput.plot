set grid

set title 'Plot for 4 subintervals'
set xlabel 'Sweep [-]'
set ylabel 'Wall Time Primal [s]'
set yrange [0:215.969]
set xrange [0:5]

## Labels
# 1 : Sweep
# 2 : PressureDrop
# 3 : Velocity Defect
# 4 : Continuity Defect
# 5 : WallTime for PimpelDyMFoam
# 6 : Total Accumulated WallTime

#set y2label "Adjoint Pressure Loss  [Nm, E-4]" 

set key top right

set style line 1 lc rgb 'black' lt 1 lw 4 pt 7 pi -1 ps 0.9
set style line 2 lc rgb 'black' lt 1 lw 1 pt 5 pi -1 ps 0.9
set style line 7 lc rgb 'black' lt 2 lw 1 pt 5 pi -1 ps 0.75

set style line 4 lt 1 lc rgb "black" pi -1 pt 7 ps 0.6 lw 2.0

set pointintervalbox 1.4

set terminal postscript eps 18 dashed lw 1 enhanced 
set output 'plot_1_5_4_intervals.eps'
plot 'logtable4.csv' using 1:5 with linespoints ls 1 title 'Primal Shooting',
