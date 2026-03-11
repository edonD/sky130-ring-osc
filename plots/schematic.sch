v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SKY130 Current-Starved Ring Oscillator — 3-stage, NMOS starving} 50 -700 0 0 0.6 0.6 {}
T {=== Stage 1 ===} 50 -660 0 0 0.4 0.4 {}
T {=== Stage 2 ===} 50 -630 0 0 0.4 0.4 {}
T {=== Stage 3 ===} 50 -600 0 0 0.4 0.4 {}
C {devices/vsource.sym} 80 -280 0 0 {name=Vdd
value=1.8}
C {devices/vsource.sym} 70 -50 0 0 {name=Vss
value=0}
C {devices/vsource.sym} 1030 -100 0 0 {name=Vctrl
value=0.9}
C {sky130_fd_pr/pfet_01v8.sym} 1300 -330 0 0 {name=XMp1
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1360 -180 0 0 {name=XMn1
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1210 -20 0 1 {name=XMs1
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1450 -340 0 1 {name=XMp2
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1630 -360 0 0 {name=XMn2
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1400 30 0 0 {name=XMs2
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1390 -460 0 0 {name=XMp3
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1550 -170 0 0 {name=XMn3
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1550 0 0 0 {name=XMs3
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1220 -180 0 1 {name=XMpout
W=5u
L=0.15u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1100 -340 0 0 {name=XMnout
W=2.5u
L=0.15u
nf=1
spiceprefix=X}
C {devices/vsource.sym} 1050 110 0 0 {name=Vkick
value=pulse(0}
C {devices/capa.sym} 1800 -220 0 0 {name=Ckick
value=5f}
N 1030 -130 1290 -130 {lab=vctrl}
N 1290 -130 1290 -30 {lab=vctrl}
N 1230 -20 1290 -20 {lab=vctrl}
N 1290 -20 1290 -30 {lab=vctrl}
N 1380 30 1290 30 {lab=vctrl}
N 1290 30 1290 -30 {lab=vctrl}
N 1530 0 1290 0 {lab=vctrl}
N 1290 0 1290 -30 {lab=vctrl}
N 1360 -150 1210 -150 {lab=ns1}
N 1210 -150 1210 -50 {lab=ns1}
N 1450 -370 1500 -370 {lab=n2}
N 1500 -370 1500 -350 {lab=n2}
N 1630 -390 1500 -390 {lab=n2}
N 1500 -390 1500 -350 {lab=n2}
N 1370 -460 1500 -460 {lab=n2}
N 1500 -460 1500 -350 {lab=n2}
N 1530 -170 1500 -170 {lab=n2}
N 1500 -170 1500 -350 {lab=n2}
N 1630 -330 1400 -330 {lab=ns2}
N 1400 -330 1400 0 {lab=ns2}
N 1550 -140 1550 -30 {lab=ns3}
N 1220 -210 1100 -210 {lab=out}
N 1100 -210 1100 -370 {lab=out}
C {devices/vdd.sym} 80 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1300 -300 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1320 -330 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1450 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1430 -340 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1390 -430 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1410 -460 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1220 -150 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1200 -180 0 0 {name=l_vdd lab=VDD}
C {devices/gnd.sym} 80 -250 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 70 -20 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1030 -70 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1050 140 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 70 -80 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1380 -180 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1210 10 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1190 -20 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1650 -360 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1400 60 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1420 30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1570 -170 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1550 30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1570 0 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1100 -310 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1120 -340 0 0 {name=l_vss lab=VSS}
C {devices/lab_pin.sym} 1300 -360 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1360 -210 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1470 -340 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1610 -360 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1800 -250 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1280 -330 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1340 -180 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1390 -490 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1550 -200 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1240 -180 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1080 -340 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1050 80 0 0 {name=l_kick sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 1800 -190 0 0 {name=l_kick sig_type=std_logic lab=kick}
