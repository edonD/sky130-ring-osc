v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SKY130 5-Stage Current-Starved Ring Oscillator} 50 -700 0 0 0.6 0.6 {}
T {=== Stage 1 ===} 50 -660 0 0 0.4 0.4 {}
T {=== Stage 2 ===} 50 -630 0 0 0.4 0.4 {}
T {=== Stage 3 ===} 50 -600 0 0 0.4 0.4 {}
T {=== Stage 4 ===} 50 -570 0 0 0.4 0.4 {}
T {=== Stage 5 ===} 50 -540 0 0 0.4 0.4 {}
C {devices/vsource.sym} 80 -280 0 0 {name=Vdd
value=1.8}
C {devices/vsource.sym} 50 -70 0 0 {name=Vss
value=0}
C {devices/vsource.sym} 1100 -60 0 0 {name=Vctrl
value=0.9}
C {sky130_fd_pr/pfet_01v8.sym} 1700 -90 0 0 {name=XMp1
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2330 -40 0 0 {name=XMn1
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1500 -50 0 1 {name=XMsn1
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {devices/capa.sym} 3000 -390 0 0 {name=Cc1
value={Cc}p}
C {sky130_fd_pr/pfet_01v8.sym} 1900 -140 0 1 {name=XMp2
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2440 -320 0 0 {name=XMn2
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2040 -290 0 0 {name=XMsn2
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {devices/capa.sym} 3000 -240 0 0 {name=Cc2
value={Cc}p}
C {sky130_fd_pr/pfet_01v8.sym} 2100 -160 0 0 {name=XMp3
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2570 -180 0 0 {name=XMn3
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2190 40 0 0 {name=XMsn3
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {devices/capa.sym} 3000 -170 0 0 {name=Cc3
value={Cc}p}
C {sky130_fd_pr/pfet_01v8.sym} 2280 -230 0 1 {name=XMp4
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2710 -170 0 0 {name=XMn4
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2280 110 0 0 {name=XMsn4
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {devices/capa.sym} 3000 -50 0 0 {name=Cc4
value={Cc}p}
C {sky130_fd_pr/pfet_01v8.sym} 2380 -180 0 0 {name=XMp5
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2480 -40 0 0 {name=XMn5
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 2600 30 0 0 {name=XMsn5
W={Ws}u
L={Ls}u
nf=1
spiceprefix=X}
C {devices/capa.sym} 3000 40 0 0 {name=Cc5
value={Cc}p}
C {sky130_fd_pr/pfet_01v8.sym} 2010 0 0 1 {name=XMpout
W=5u
L=0.15u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1300 -50 0 0 {name=XMnout
W=2.5u
L=0.15u
nf=1
spiceprefix=X}
C {devices/vsource.sym} 1100 280 0 0 {name=Vkick
value=pulse(0}
C {devices/capa.sym} 3000 210 0 0 {name=Ckick
value=5f}
N 2440 -290 2040 -290 {lab=sn2}
N 2040 -290 2040 -320 {lab=sn2}
N 2570 -150 2190 -150 {lab=sn3}
N 2190 -150 2190 10 {lab=sn3}
N 2710 -140 2280 -140 {lab=sn4}
N 2280 -140 2280 80 {lab=sn4}
N 2480 -10 2600 -10 {lab=sn5}
N 2600 -10 2600 0 {lab=sn5}
N 2010 -30 1300 -30 {lab=out}
N 1300 -30 1300 -80 {lab=out}
C {devices/vdd.sym} 80 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1700 -60 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1720 -90 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1900 -110 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1880 -140 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2100 -130 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2120 -160 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2280 -200 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2260 -230 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2380 -150 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2400 -180 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 2010 30 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1990 0 0 0 {name=l_vdd lab=VDD}
C {devices/gnd.sym} 80 -250 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -40 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1100 -30 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1100 310 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2350 -40 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1500 -20 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1480 -50 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2460 -320 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2040 -260 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2060 -290 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2590 -180 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2190 70 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2210 40 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2730 -170 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2280 140 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2300 110 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2500 -40 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2600 60 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 2620 30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1300 -20 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1320 -50 0 0 {name=l_vss lab=VSS}
C {devices/lab_pin.sym} 1100 -90 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1520 -50 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2020 -290 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2170 40 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2260 110 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 2580 30 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1700 -120 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 2330 -70 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 3000 -420 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1920 -140 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 2420 -320 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 3000 -20 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 3000 180 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1680 -90 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2310 -40 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 3000 -140 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2380 -210 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2480 -70 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 3000 10 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2030 0 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 1280 -50 0 0 {name=l_n5 sig_type=std_logic lab=n5}
C {devices/lab_pin.sym} 2330 -10 0 0 {name=l_sn1 sig_type=std_logic lab=sn1}
C {devices/lab_pin.sym} 1500 -80 0 0 {name=l_sn1 sig_type=std_logic lab=sn1}
C {devices/lab_pin.sym} 3000 -360 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 2100 -190 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 2570 -210 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 3000 -200 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 2300 -230 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 2690 -170 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1900 -170 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 2440 -350 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 3000 -270 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 2080 -160 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 2550 -180 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 3000 70 0 0 {name=l_n2 sig_type=std_logic lab=n2}
C {devices/lab_pin.sym} 3000 -210 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 2280 -260 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 2710 -200 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 3000 -80 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 2360 -180 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 2460 -40 0 0 {name=l_n4 sig_type=std_logic lab=n4}
C {devices/lab_pin.sym} 1100 250 0 0 {name=l_kick sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 3000 240 0 0 {name=l_kick sig_type=std_logic lab=kick}
