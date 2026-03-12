v {xschem version=3.4.5 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SKY130 Complementary Current-Starved Ring Oscillator — 3-stage} 50 -700 0 0 0.6 0.6 {}
T {=== Current mirror bias ===} 50 -660 0 0 0.4 0.4 {}
T {=== Stage 1 ===} 50 -630 0 0 0.4 0.4 {}
T {=== Stage 2 ===} 50 -600 0 0 0.4 0.4 {}
T {=== Stage 3 ===} 50 -570 0 0 0.4 0.4 {}
C {devices/vsource.sym} 80 -280 0 0 {name=Vdd
value=1.8}
C {devices/vsource.sym} 50 -70 0 0 {name=Vss
value=0}
C {devices/vsource.sym} 1070 -140 0 0 {name=Vctrl
value=0.9}
C {sky130_fd_pr/nfet_01v8.sym} 1270 -80 0 1 {name=XMref_n
W={Wbn}u
L={Lbn}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1290 -310 0 0 {name=XMref_p
W={Wbp}u
L={Lbp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1430 -400 0 0 {name=XMp1
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1540 -310 0 0 {name=XMn1
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1320 -520 0 1 {name=XMsp1
W={Wsp}u
L={Lsp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1420 -30 0 0 {name=XMsn1
W={Wsn}u
L={Lsn}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1550 -470 0 0 {name=XMp2
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1680 -280 0 0 {name=XMn2
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1380 -190 0 0 {name=XMsp2
W={Wsp}u
L={Lsp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1610 10 0 0 {name=XMsn2
W={Wsn}u
L={Lsn}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1690 -490 0 0 {name=XMp3
W={Wp}u
L={Lp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1580 -150 0 0 {name=XMn3
W={Wn}u
L={Ln}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1830 -350 0 0 {name=XMsp3
W={Wsp}u
L={Lsp}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1740 -100 0 0 {name=XMsn3
W={Wsn}u
L={Lsn}u
nf=1
spiceprefix=X}
C {sky130_fd_pr/pfet_01v8.sym} 1140 -410 0 0 {name=XMpout
W=5u
L=0.15u
nf=1
spiceprefix=X}
C {sky130_fd_pr/nfet_01v8.sym} 1210 -260 0 0 {name=XMnout
W=2.5u
L=0.15u
nf=1
spiceprefix=X}
C {devices/vsource.sym} 1100 40 0 0 {name=Vkick
value=pulse(0}
C {devices/capa.sym} 2000 -280 0 0 {name=Ckick
value=5f}
N 1430 -370 1320 -370 {lab=sp1}
N 1320 -370 1320 -550 {lab=sp1}
N 1540 -280 1420 -280 {lab=sn1}
N 1420 -280 1420 -60 {lab=sn1}
N 1550 -500 1620 -500 {lab=n2}
N 1620 -500 1620 -360 {lab=n2}
N 1680 -310 1620 -310 {lab=n2}
N 1620 -310 1620 -360 {lab=n2}
N 1670 -490 1620 -490 {lab=n2}
N 1620 -490 1620 -360 {lab=n2}
N 1560 -150 1620 -150 {lab=n2}
N 1620 -150 1620 -360 {lab=n2}
N 1550 -440 1380 -440 {lab=sp2}
N 1380 -440 1380 -220 {lab=sp2}
N 1680 -250 1610 -250 {lab=sn2}
N 1610 -250 1610 -20 {lab=sn2}
N 1690 -460 1830 -460 {lab=sp3}
N 1830 -460 1830 -380 {lab=sp3}
N 1580 -120 1740 -120 {lab=sn3}
N 1740 -120 1740 -130 {lab=sn3}
N 1140 -440 1210 -440 {lab=out}
N 1210 -440 1210 -290 {lab=out}
C {devices/vdd.sym} 80 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1290 -280 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1310 -310 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1450 -400 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1320 -490 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1300 -520 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1570 -470 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1380 -160 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1400 -190 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1710 -490 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1830 -320 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1850 -350 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1140 -380 0 0 {name=l_vdd lab=VDD}
C {devices/vdd.sym} 1160 -410 0 0 {name=l_vdd lab=VDD}
C {devices/gnd.sym} 80 -250 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -40 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1070 -110 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 1100 70 0 0 {name=l_0 lab=GND}
C {devices/gnd.sym} 50 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1270 -50 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1250 -80 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1560 -310 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1420 0 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1440 -30 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1700 -280 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1610 40 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1630 10 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1600 -150 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1740 -70 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1760 -100 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1210 -230 0 0 {name=l_vss lab=VSS}
C {devices/gnd.sym} 1230 -260 0 0 {name=l_vss lab=VSS}
C {devices/lab_pin.sym} 1070 -170 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1290 -80 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1400 -30 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1590 10 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1720 -100 0 0 {name=l_vctrl sig_type=std_logic lab=vctrl}
C {devices/lab_pin.sym} 1270 -110 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1290 -340 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1270 -310 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1340 -520 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1360 -190 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1810 -350 0 0 {name=l_pbias sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1430 -430 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1540 -340 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1530 -470 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1660 -280 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 2000 -310 0 0 {name=l_n1 sig_type=std_logic lab=n1}
C {devices/lab_pin.sym} 1410 -400 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1520 -310 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1690 -520 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1580 -180 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1120 -410 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1190 -260 0 0 {name=l_n3 sig_type=std_logic lab=n3}
C {devices/lab_pin.sym} 1100 10 0 0 {name=l_kick sig_type=std_logic lab=kick}
C {devices/lab_pin.sym} 2000 -250 0 0 {name=l_kick sig_type=std_logic lab=kick}
