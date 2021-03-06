
pro lsst_flat_image, filename, flux, exptime, $
   DEFECTFILE=defectfile, DPIXPCT=dpixpct, BPIXVAL=bpixval, $
   OFFSET=offset, GAIN=gain, RDNOISE=rdnoise, POISSON=poisson, $
   SEG_COLS=seg_cols, SEG_ROWS=seg_rows, $
   PRE_COLS=pre_cols, OVER_COLS=over_cols, OVER_ROWS=over_rows, $
   VERBOSE=verbose

;+
 ; NAME:
 ;   LSST_FLAT_IMAGE
 ;
 ; PURPOSE:
 ;   Create a 16 extension FITS file simulated flat field image
 ;
 ; EXPLANATION:
 ;   
 ;   
 ; CALLING SEQUENCE:
 ;    LSST_FLAT_IMAGE, filename, flux, exptime [ ,
 ;       DEFECTFILE=defectfile, DPIXPCT=dpixpct, BPIXVAL=bpixval, 
 ;       OFFSET=offset, GAIN=gain, RDNOISE=rdnoise, POISSON=poisson, 
 ;       SEG_COLS=seg_cols, SEG_ROWS=seg_rows, 
 ;       PRE_COLS=pre_cols, OVER_COLS=over_cols, OVER_ROWS=over_rows, 
 ;       VERBOSE=verbose ]
 ;
 ; INPUTS:
 ;    filename: name of the file to create
 ;
 ; OPTIONAL INPUTS:
 ;
 ; INPUT KEYWORD PARAMETERS:
 ;    DEFECTFILE : if set, use specified file to add bright defects to bias image
 ;    DPIXPCT : percent of local median for dark pixel value
 ;    BPIXVAL : value to set any bright defects to
 ;    OFFSET  : image bias offset in DN
 ;    GAIN    : system gain, e-/DN
 ;    RDNOISE : system read noise in e-
 ;    SEG_COLS: number of imaging columns in each segment, default = 512
 ;    SEG_ROWS: number of imaging rows in each segment, default = 2002
 ;    PRE_COLS:  number of prescan columns in image segment, default=10
 ;    OVER_COLS: number of overscan columns in image segment, default=20
 ;    OVER_ROWS: number of overscan rows in image segment, default=20
 ;    CHAN_ID: if set, make all pixels in extension equal to extension number, not pixval
 ;    VERBOSE: if set, print some diagnostics
 ;    
 ; OUTPUT KEYWORD PARAMETERS:
 ;    NONE
 ;
 ; EXAMPLES:
 ;
 ;
 ; HISTORY:
 ; Written by: P. Doherty  April, 2013
 ;
 ;-
 ;-----------------------------------------------------------------------------   
compile_opt IDL2

if N_Params() NE 3 then begin
  print,'LSST_FLAT_IMAGE: Incorrect number of parameters. Exiting.'
  return
endif

IF N_Elements(offset)    EQ 0 THEN offset = 1000    ; image bias offset in DN
IF N_Elements(gain)      EQ 0 THEN gain = 5.0       ; system gain in e-/DN
IF N_Elements(rdnoise)   EQ 0 THEN rdnoise = 7.0    ; system read noise in e-
IF N_Elements(dpixpct)   EQ 0 THEN dpixpct = 0.75   ; just a little too dark
IF N_Elements(bpixval)   EQ 0 THEN bpixval = 65000  ; really bright pixels!
IF N_Elements(seg_cols)  EQ 0 THEN seg_cols  = 512
IF N_Elements(seg_rows)  EQ 0 THEN seg_rows  = 2002
IF N_Elements(pixval)    EQ 0 THEN pixval    = 0
IF N_Elements(pre_cols)  EQ 0 THEN pre_cols  = 10
IF N_Elements(over_cols) EQ 0 THEN over_cols = 20
IF N_Elements(over_rows) EQ 0 THEN over_rows = 20
if keyword_set(POISSON) then poisson = 1 else poisson = 0
if keyword_set(VERBOSE) then verbose = 1 else verbose = 0

gain = float(gain)
rdnoise = float(rdnoise)

lsst_bias_image, filename, $
   OFFSET=offset, GAIN=gain, RDNOISE=rdnoise, $ 
   SEG_COLS=seg_cols, SEG_ROWS=seg_rows, $
   PRE_COLS=pre_cols, OVER_COLS=over_cols, OVER_ROWS=over_rows, $
   VERBOSE=verbose

; update the primary header with potentially useful information
fits_read, filename, im, hdr, EXTEN_NO=0
SXADDPAR, hdr, 'FLUX    ', flux   , 'e-/sec', FORMAT='(F8.3)'
SXADDPAR, hdr, 'EXPTIME ', exptime, 'exposure time', FORMAT='(F8.3)'
MODFITS, filename, 0, hdr, EXTEN_NO=0

; add signal to the image based no exposure time and flux
for i = 1, 16 do begin
   seg_expose, filename, i, flux, exptime, GAIN=gain, POISSON=poisson, $
      PRE_COLS=pre_cols, OVER_COLS=over_cols, OVER_ROWS=over_rows, $
      VERBOSE=verbose
endfor
  
; if defectfile is provided, add defects including bright, dark, dead, 
; and trap pixels
IF N_Elements(defectfile) EQ 1 THEN begin
lsst_apply_defects, filename, defectfile,  $
   BPIXVAL=65000, DPIXPCT=dpixpct, $
   PRE_COLS=pre_cols, OVER_COLS=over_cols, OVER_ROWS=over_rows, $
   VERBOSE=verbose, /bright, /dark, /dead, /traps
endif

end