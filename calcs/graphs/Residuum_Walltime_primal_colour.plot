set grid

#set title 'Plot Comparison over [2, 4, 5, 10, 20] subintervals'
set xlabel 'Walltime [s]'
set ylabel 'Impulsdefekt [kg m/s]'
set yrange [0:220]
set xrange [00:3500]

## Labels
# 1 : Sweep
# 2 : PressureDrop
# 3 : Velocity Defect
# 4 : Continuity Defect
# 5 : WallTime for PimpelDyMFoam
# 6 : Total Accumulated WallTime

#set y2label "Adjoint Pressure Loss  [Nm, E-4]" 

#set key top right
set key top right

#set arrow from 1291.4,0 to 1291.4,3.0e-07 nohead lc rgb "red" dt 4 pt 5 pi -1 ps 0.9
set arrow from 1291.4,0 to 1291.4,220 lc rgb "black" lt 1 lw 1.5 dt 4 nohead
set label 'Walltime' at 1080,150
set label 'Referenz' at 1080,140
set style line 1 lc rgb 'black' lt 1 lw 4 pt 7 pi -1 ps 0.9
set style line 2 lc rgb 'black' lt 1 lw 1 pt 5 pi -1 ps 0.9
set style line 7 lc rgb 'black' lt 2 lw 1 pt 5 pi -1 ps 0.75

set style line 4 lt 1 lc rgb "black" pi -1 pt 7 ps 0.6 lw 2.0

set pointintervalbox 1.4

set terminal jpeg
#set terminal postscript eps 18 dashed lw 1 enhanced 
#set output 'plot_1_2_Comparison_intervals.eps'
set output 'Residuum_Walltime_primal.jpg'
f(x)=1.0928e-07
g(y)=1291.4
#set arrow from 400,1.0928e-07 to 1600,1.0928e-07 nohead lc rgb "red" dt 4 title 'Referenz Druckverlustarbeit'
#set arrow from 1291.4,0 to 1291.4,220 lc rgb "red" lt 1 lw 2 dt 4 nohead
plot '2_timeparallel_1/logtable2.csv' using 6:3 with linespoints lc rgb 'green' title '2 Intervalle' , \
'4_timeparallel_1/logtable4.csv' using 6:3 with linespoints lc rgb 'orange' title '4 Intervalle' , \
'5_timeparallel_1/logtable5.csv' using 6:3 with linespoints lc rgb 'blue'  title '5 Intervalle' , \
'10_timeparallel_1/logtable10.csv' using 6:3 with linespoints lc rgb 'black' title '10 Intervalle' , \
'20_timeparallel_1/logtable20.csv' using 6:3 with linespoints lc rgb 'cyan'  title '20 Intervalle', \

#f(x) with linespoint lc rgb "blue" title 'Referenz'

