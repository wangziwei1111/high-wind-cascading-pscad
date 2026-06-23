
#------------------------------------------------------------------------------
# Project '3IBR' make using the 'GFortran 4.6' compiler.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# All project
#------------------------------------------------------------------------------

all: targets
	@echo !--Make: succeeded.



#------------------------------------------------------------------------------
# Directories, Platform, and Version
#------------------------------------------------------------------------------

Arch        = windows
EmtdcDir    = C:\PROGRA~2\PSCAD46\emtdc\gf46
EmtdcInc    = $(EmtdcDir)\inc
EmtdcBin    = $(EmtdcDir)\$(Arch)
EmtdcMain   = $(EmtdcBin)\main.obj
EmtdcLib    = $(EmtdcBin)\emtdc.lib


#------------------------------------------------------------------------------
# Fortran Compiler
#------------------------------------------------------------------------------

FC_Name         = gfortran.exe
FC_Suffix       = o
FC_Args         = -c -ffree-form -fdefault-real-8
FC_Debug        = 
FC_Preprocess   = -xf95-cpp-input 
FC_Preproswitch = 
FC_Warn         = -Wconversion
FC_Checks       = 
FC_Includes     = -I"$(EmtdcInc)" -I"$(EmtdcBin)"
FC_Compile      = $(FC_Name) $(FC_Args) $(FC_Preprocess) $(FC_Preproswitch) $(FC_Includes) $(FC_Debug) $(FC_Warn) $(FC_Checks)

#------------------------------------------------------------------------------
# C Compiler
#------------------------------------------------------------------------------

CC_Name     = gcc.exe
CC_Suffix   = o
CC_Args     = -c
CC_Debug    = 
CC_Includes = -I"$(EmtdcInc)" -I"$(EmtdcBin)"
CC_Compile  = $(CC_Name) $(CC_Args) $(CC_Includes) $(CC_Debug)

#------------------------------------------------------------------------------
# Linker
#------------------------------------------------------------------------------

Link_Name   = gcc.exe
Link_Debug  = 
Link_Args   = -o $@
Link        = $(Link_Name) $(Link_Args) $(Link_Debug)

#------------------------------------------------------------------------------
# Build rules for generated files
#------------------------------------------------------------------------------


%.$(FC_Suffix): %.f
	@echo !--Compile: $<
	$(FC_Compile) $<


%.$(CC_Suffix): %.c
	@echo !--Compile: $<
	$(CC_Compile) $<



#------------------------------------------------------------------------------
# Build rules for file references
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# Dependencies
#------------------------------------------------------------------------------


FC_Objects = \
 Station.$(FC_Suffix) \
 Main.$(FC_Suffix) \
 P1.$(FC_Suffix) \
 P2.$(FC_Suffix) \
 P3.$(FC_Suffix) \
 G_38_0_1_DYR.$(FC_Suffix) \
 G_37_0_1_DYR.$(FC_Suffix) \
 G_34_0_1_DYR.$(FC_Suffix) \
 G_32_0_1_DYR.$(FC_Suffix) \
 G_31_0_1_DYR.$(FC_Suffix) \
 G_33_0_1_DYR.$(FC_Suffix) \
 G_39_0_1_DYR.$(FC_Suffix) \
 G_36_0_1_DYR.$(FC_Suffix) \
 G_35_0_1_DYR.$(FC_Suffix) \
 REPC_A_1.$(FC_Suffix) \
 IBR_AVM_2_1_1.$(FC_Suffix) \
 REEC_A_1_2_1_1.$(FC_Suffix) \
 CurrentLimit_1_2_1_1.$(FC_Suffix) \
 REGC_A_1_2_1_1.$(FC_Suffix)

FC_ObjectsLong = \
 "Station.$(FC_Suffix)" \
 "Main.$(FC_Suffix)" \
 "P1.$(FC_Suffix)" \
 "P2.$(FC_Suffix)" \
 "P3.$(FC_Suffix)" \
 "G_38_0_1_DYR.$(FC_Suffix)" \
 "G_37_0_1_DYR.$(FC_Suffix)" \
 "G_34_0_1_DYR.$(FC_Suffix)" \
 "G_32_0_1_DYR.$(FC_Suffix)" \
 "G_31_0_1_DYR.$(FC_Suffix)" \
 "G_33_0_1_DYR.$(FC_Suffix)" \
 "G_39_0_1_DYR.$(FC_Suffix)" \
 "G_36_0_1_DYR.$(FC_Suffix)" \
 "G_35_0_1_DYR.$(FC_Suffix)" \
 "REPC_A_1.$(FC_Suffix)" \
 "IBR_AVM_2_1_1.$(FC_Suffix)" \
 "REEC_A_1_2_1_1.$(FC_Suffix)" \
 "CurrentLimit_1_2_1_1.$(FC_Suffix)" \
 "REGC_A_1_2_1_1.$(FC_Suffix)"

CC_Objects =

CC_ObjectsLong =

UserLibs = C:\PSCAD_~1\PN9446~1\PSCAD\ETRAN_~1.LIB


SysLibs  = -lgfortran -lstdc++ -lwsock32

Binary   = 3IBR.exe

$(Binary): $(FC_Objects) $(CC_Objects) $(UserLibs)
	@echo !--Link: $@
	$(Link) "$(EmtdcMain)" *.$(CC_Suffix) $(UserLibs) "$(EmtdcLib)" $(SysLibs)

targets: $(Binary)


clean:
	-del EMTDC_V*
	-del *.obj
	-del *.o
	-del *.exe
	@echo !--Make clean: succeeded.



