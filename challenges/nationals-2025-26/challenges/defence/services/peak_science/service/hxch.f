      PROGRAM HXCH
      INTEGER PS,X,Y,RT,MS
      REAL IV,CV,DT,K
      COMMON/CD/PS,IV,X,Y,CV,DT,MS,K
      GOTO 2
C     USE RT 100 FOR UNPLANNED EXIT. SHOULDN'T HAPPEN THO
C     MY SCIENCE MODEL IS PERFECT
      CALL FLUSH()
1     STOP 0
2     CALL RC()
      IF(PS<=2.OR.PS>20)THEN
      PRINT*,"DIM ERROR"
      RT=1
      GOTO 1
      ENDIF
      IF(X<=0.OR.X>PS)THEN
      PRINT*,"COORD ERROR"
      RT=2
      GOTO 1
      ENDIF
      IF(Y<=0.OR.Y>PS)THEN
      PRINT*,"COORD ERROR"
      RT=2
      GOTO 1
      ENDIF
      IF(MS<0.OR.MS>10)THEN
      PRINT*,"STEP<0 OR STEP>10"
      RT=3
      GOTO 1
      ENDIF
      IF(DT<=0.0.OR.DT>0.5)THEN
      PRINT*,"DT<=0.0 OR DT>0.5"
      RT=3
      GOTO 1
      ENDIF
      IF(K<0.0.OR.K>1.0)THEN
      PRINT*,"K<0.0 OR K>1.0"
      RT=4
      GOTO 1
      ENDIF
      CALL FF()
      CALL RUN()
      PRINT*,"Execution completed"
      STOP 0
      END

C   LOOK AT THIS BAD BOY, IT CAN STORE
CUP TO 64 BYTE. RAM THESE DAYS
C     IS INCREDIBLE
      SUBROUTINE FF()
      INTEGER PI
      CHARACTER*64 FN,FNN
      CHARACTER*128 TE
      COMMON/TF/FN,TE,PI,FNN
      PI=GETPID()
      WRITE(FN,'("/tmp/rf",I0)')PI
      WRITE(FNN,'("/tmp/rf_nr_",I0)')PI
      WRITE(TE,'("./trtm < ",A)')TRIM(FN)
      END

      SUBROUTINE RC()
      INTEGER PS,X,Y,RT,MS
      REAL IV,CV,DT,K
      COMMON/CD/PS,IV,X,Y,CV,DT,MS,K
      READ(*,*)PS
      READ(*,*)IV
      READ(*,*)X
      READ(*,*)Y
      READ(*,*)CV
      READ(*,*)DT
      READ(*,*)MS
      READ(*,*)K
      END

      SUBROUTINE RUN()
      INTEGER PS,X,Y,MS,TRC,PI,IOS
      LOGICAL TF,END,DIC
      EQUIVALENCE(TRC,TF)
      REAL IV,CV,DT,A,K,MEC,DI
      REAL*4D(PS*PS)
      REAL*4DE(PS*PS)
      CHARACTER*64 FN,DC,FNN,P
      CHARACTER*128 TE
      COMMON/CD/PS,IV,X,Y,CV,DT,MS,K
      COMMON/TF/FN,TE,PI,FNN
      A=DT*K
      DO I=1,PS*PS
      D(I)=IV
      ENDDO
      D(PS*(Y-1)+X)=CV
      DO ST=1,MS
      DO I=2,PS-1
      DO J=2,PS-1
      DE(PS*(J-1)+I)=A*(-4*D(PS*(J-1)+I)+D(PS*(J-1)+I+1)+
     +D(PS*(J-1)+I-1)+D(PS*(J)+I)+D(PS*(J-2)+I))
      ENDDO
      DE(I)=A*(-3*D(I)+D(I-1)+D(I+1)+D(PS+I))
      DE(PS*(PS-1)+I)=A*(-3*D(PS*(PS-1)+I)+D(PS*(PS-1)+I-1)+
     +D(PS*(PS-1)+I+1)+D(PS*(PS-2)+I))
      DE(PS*(I-1)+1)=A*(-3*D(PS*(I-1)+1)+D(PS*(I-1)+2)+
     +D(PS*I+1)+D(PS*(I-2)+1))
      DE(PS*I)=A*(-3*D(PS*I)+D(PS*I-1)+D(PS*(I+1))+D(PS*(I-1)))
      ENDDO
      DE(1)=A*(-2*D(1)+D(2)+D(PS+1))
      DE(PS)=A*(-2*D(PS)+D(PS-1)+D(2*PS))
      DE(PS*(PS-1)+1)=A*(-2*D(PS*(PS-1)+1)+D(PS*(PS-1)+2)+
     +D(PS*(PS-2)+1))
      DE(PS*PS)=A*(-2*D(PS*PS)+D(PS*PS-1)+D(PS*(PS-1)))
      DO I=1,PS*PS
      D(I)=D(I)+DE(I)
      ENDDO
      ENDDO
      OPEN(UNIT=10,FILE=FN)
      WRITE(10,*)PI
      WRITE(10,*)PS
      WRITE(10,*)(D(I),I=1,PS*PS)
      CLOSE(10)
      CALL SYSTEM(TE,TRC)
      OPEN(UNIT=10,FILE=FN)
      CLOSE(10,STATUS='DELETE')
      TRC=ISHFT(TRC,-8)
      OPEN(10,FILE=FNN)
      READ(10,*)MEC
      READ(10,*)END
      READ(10,*)DI
      READ(10,*)DIC
      CLOSE(10,STATUS='DELETE')
      READ(*,'(A)',IOSTAT=IOS)DC
      IF((TF.OR.(.NOT.DI>0.005.AND.DIC)).AND.IOS==0)THEN
c     THIS HELP ME DEBUG ... ERM VISUALIZE PROBLEMS
      CALL SYSTEM(DC)
      ENDIF
      IF(END)THEN
      PRINT*,"Danger, Will Robinson"
      OPEN(11,FILE="./pswd",STATUS='OLD',IOSTAT=IOS)
      IF(IOS/=0)THEN
      STOP 100
      ENDIF
      READ(11,'(A)')P
      PRINT*,"Password to activate emergency mesure:"
      PRINT*,P
      CLOSE(11)
      ENDIF
      RETURN
      END
