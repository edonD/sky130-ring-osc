v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SKY130 5-Stage Current-Starved Ring Oscillator} 50 -700 0 0 0.6 0.6 {}
T {5 stages: lower per-stage gain requirement, better jitter} 50 -660 0 0 0.4 0.4 {}
T {=== Stage 1 ===} 50 -630 0 0 0.4 0.4 {}
T {=== Stage 2 ===} 50 -600 0 0 0.4 0.4 {}
T {=== Stage 3 ===} 50 -570 0 0 0.4 0.4 {}
T {=== Stage 4 ===} 50 -540 0 0 0.4 0.4 {}
T {=== Stage 5 ===} 50 -510 0 0 0.4 0.4 {}
C {devices/vsource.sym} 80 -280 0 0 {name=Vdd
value=1.8}
C {devices/vsource.sym} 50 -70 0 0 {name=Vss
value=0}
C {devices/vsource.sym} 1100 -160 0 0 {name=Vctrl
value=0.9}
C {sky130_fd_pr/pfet_01v8.sym} 1670 -300 0 0 {name=XMp1
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1810 -220 0 0 {name=XMn1
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1500 -160 0 1 {name=XMsn1
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1780 -400 0 1 {name=XMp2
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1970 -190 0 0 {name=XMn2
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1860 0 0 0 {name=XMsn2
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1960 -520 0 0 {name=XMp3
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2100 -300 0 0 {name=XMn3
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2080 -30 0 0 {name=XMsn3
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 2130 -490 0 1 {name=XMp4
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2260 -390 0 0 {name=XMn4
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2200 -140 0 0 {name=XMsn4
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1950 -330 0 0 {name=XMp5
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2400 -270 0 0 {name=XMn5
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2600 -150 0 0 {name=XMsn5
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1670 -130 0 1 {name=XMpout
W=5u
L=0.15u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1300 -240 0 0 {name=XMnout
W=2.5u
L=0.15u
nf=1
spiceprefix=X}
C {devices/vsource.sym} 1100 30 0 0 {name=Vkick
value=pulse(0}
C {devices/capa.sym} 3000 -200 0 0 {name=Ckick
value=5f}
N 1810 -190 1500 -190 {lab=sn1}
N 1780 -430 1940 -430 {lab=n2}
N 1940 -430 1940 -370 {lab=n2}
N 1970 -220 1940 -220 {lab=n2}
N 1940 -220 1940 -370 {lab=n2}
N 1940 -520 1940 -370 {lab=n2}
N 2080 -300 1940 -300 {lab=n2}
N 1940 -300 1940 -370 {lab=n2}
N 1970 -160 1860 -160 {lab=sn2}
N 1860 -160 1860 -30 {lab=sn2}
N 1960 -550 2110 -550 {lab=n3}
N 2110 -550 2110 -440 {lab=n3}
N 2100 -330 2110 -330 {lab=n3}
N 2110 -330 2110 -440 {lab=n3}
N 2150 -490 2110 -490 {lab=n3}
N 2110 -490 2110 -440 {lab=n3}
N 2240 -390 2110 -390 {lab=n3}
N 2110 -390 2110 -440 {lab=n3}
N 2100 -270 2080 -270 {lab=sn3}
N 2080 -270 2080 -60 {lab=sn3}
N 2130 -520 2180 -520 {lab=n4}
N 2180 -520 2180 -380 {lab=n4}
N 2260 -420 2180 -420 {lab=n4}
N 2180 -420 2180 -380 {lab=n4}
N 1930 -330 2180 -330 {lab=n4}
N 2180 -330 2180 -380 {lab=n4}
N 2380 -270 2180 -270 {lab=n4}
N 2180 -270 2180 -380 {lab=n4}
N 2260 -360 2200 -360 {lab=sn4}
N 2200 -360 2200 -170 {lab=sn4}
N 2400 -240 2600 -240 {lab=sn5}
N 2600 -240 2600 -180 {lab=sn5}
N 1670 -160 1300 -160 {lab=out}
N 1300 -160 1300 -270 {lab=out}
C {devices/vdd.sym} 80 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1670 -270 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1690 -300 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1780 -370 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1760 -400 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1960 -490 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1980 -520 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2130 -460 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2110 -490 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1950 -300 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1970 -330 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1670 -100 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1650 -130 0 0 {name=l_vdd lab=VDD}
C {devices/gnd.sym} 80 -250 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -40 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1100 -130 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1100 60 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1830 -220 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1500 -130 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1480 -160 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1990 -190 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1860 30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1880 0 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2120 -300 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2080 0 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2100 -30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2280 -390 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2200 -110 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2220 -140 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2420 -270 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2600 -120 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2620 -150 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1300 -210 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1320 -240 0 0 {name=l_vss lab=VSS}
C {devices/lab_pin.sym} 1100 -190 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1520 -160 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1840 0 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2060 -30 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2180 -140 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2580 -150 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1670 -330 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1810 -250 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1800 -400 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1950 -190 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 3000 -230 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1650 -300 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1790 -220 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1950 -360 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2400 -300 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1690 -130 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1280 -240 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1100 0 0 0 {name=l_kick sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 3000 -170 0 0 {name=l_kick sig_type=std_logic lab=kick}
