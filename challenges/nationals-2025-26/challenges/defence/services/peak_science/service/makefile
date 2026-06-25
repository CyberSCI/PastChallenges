NAME=heat-exchange

HXCH_SRC=hxch.f
HXCH_TARGET=hxch

TRTM_SRC=trtm.f
TRTM_TARGET=trtm

NLZR_SRC=nlzr.f
NLZR_TARGET=nlzr

FC=gfortran
FFLAGS=-std=legacy

all: hxch_program trtm_program nlzr_program

hxch_program: $(HXCH_SRC)
	$(FC) $(FFLAGS) -o $(HXCH_TARGET) $(HXCH_SRC)

trtm_program: $(TRTM_SRC)
	$(FC) $(FFLAGS) -o $(TRTM_TARGET) $(TRTM_SRC)

nlzr_program: $(NLZR_SRC)
	$(FC) $(FFLAGS) -o $(NLZR_TARGET) $(NLZR_SRC)

clean:
	rm -f $(BIN)
