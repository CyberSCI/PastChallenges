      PROGRAM TRTM
      INTEGER SP,PI
      READ(*,*)PI
      READ(*,*)SP
      CALL RUN(SP,PI)
      END

      SUBROUTINE RUN(SP,PI)
      INTEGER SP,PI,IB,II
      REAL EN,IN,DEVN
      EQUIVALENCE(IB,IN)
      DATA IB/Z'7F800000'/
      CHARACTER*64 FN
      CHARACTER*128 NE
      COMMON/NF/FN,NE
      REAL*4D(SP*SP)
      READ(*,*)(D(I),I=1,SP*SP)
      EN=E(SP,D)
      II=.NOT.(EN<IN)
      DEVN=DEV(SP,D)
      CALL FF(PI)
      OPEN(UNIT=20,FILE=FN)
      WRITE(20,*)EN
      WRITE(20,*)DEVN
      WRITE(20,*)SP
      WRITE(20,*)PI
      CLOSE(20,STATUS='KEEP')
      CALL SYSTEM(NE)
      OPEN(UNIT=20,FILE=FN)
      CLOSE(20,STATUS='DELETE')
      CALL EXIT(II)
      END

      SUBROUTINE FF(PI)
      INTEGER PI
      CHARACTER*64 FN
      CHARACTER*128 NE
      COMMON/NF/FN,NE
      WRITE(FN,'("/tmp/rf_n_",I0)')PI
      WRITE(NE,'("./nlzr < ",A)')TRIM(FN)
      END

      FUNCTION E(SP,D)
      INTEGER SP
      REAL E
      REAL*4D(SP*SP)
      E=0.0
      DO 10I=1,SP*SP
      E=E+D(I)*D(I)
10    CONTINUE
      E=SQRT(E)
      RETURN
      END

      FUNCTION DEV(SP,D)
      INTEGER SP
      REAL DEV,M1,M2
      REAL*4D(SP*SP)
      M1=D(1)
      M2=D(1)
      DO 10I=1,SP*SP
      IF(D(I)<M1)THEN
      GOTO 11
      ENDIF
      IF(D(I)>M2)THEN
      GOTO 12
      ENDIF
11    M1=D(I)
      GOTO 13
12    M2=D(I)
      GOTO 13
13    GOTO 10
10    CONTINUE
      DEV=M2-M1
      RETURN
      END