* OPENX64FORM.PRG -- open the x64base-generated form in the VFP Form Designer.
* Lane AIF-120. Run this INSIDE Visual FoxPro, not in PowerShell:
*     DO d:\code\ccode\tools\vfp\generated\OPENX64FORM.PRG
*
* The form's DataEnvironment cursor names students.dbf, so the data directory
* has to be on the VFP path before the designer resolves it.

SET PATH TO d:\code\ccode\dottalkpp\data\dbf\vfp
MODIFY FORM d:\code\ccode\tools\vfp\generated\x64form.scx
