# Generated from Smali.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .SmaliParser import SmaliParser
else:
    from SmaliParser import SmaliParser

# This class defines a complete listener for a parse tree produced by SmaliParser.
class SmaliListener(ParseTreeListener):

    # Enter a parse tree produced by SmaliParser#sFiles.
    def enterSFiles(self, ctx:SmaliParser.SFilesContext):
        pass

    # Exit a parse tree produced by SmaliParser#sFiles.
    def exitSFiles(self, ctx:SmaliParser.SFilesContext):
        pass


    # Enter a parse tree produced by SmaliParser#sFile.
    def enterSFile(self, ctx:SmaliParser.SFileContext):
        pass

    # Exit a parse tree produced by SmaliParser#sFile.
    def exitSFile(self, ctx:SmaliParser.SFileContext):
        pass


    # Enter a parse tree produced by SmaliParser#sSource.
    def enterSSource(self, ctx:SmaliParser.SSourceContext):
        pass

    # Exit a parse tree produced by SmaliParser#sSource.
    def exitSSource(self, ctx:SmaliParser.SSourceContext):
        pass


    # Enter a parse tree produced by SmaliParser#sSuper.
    def enterSSuper(self, ctx:SmaliParser.SSuperContext):
        pass

    # Exit a parse tree produced by SmaliParser#sSuper.
    def exitSSuper(self, ctx:SmaliParser.SSuperContext):
        pass


    # Enter a parse tree produced by SmaliParser#sInterface.
    def enterSInterface(self, ctx:SmaliParser.SInterfaceContext):
        pass

    # Exit a parse tree produced by SmaliParser#sInterface.
    def exitSInterface(self, ctx:SmaliParser.SInterfaceContext):
        pass


    # Enter a parse tree produced by SmaliParser#sMethod.
    def enterSMethod(self, ctx:SmaliParser.SMethodContext):
        pass

    # Exit a parse tree produced by SmaliParser#sMethod.
    def exitSMethod(self, ctx:SmaliParser.SMethodContext):
        pass


    # Enter a parse tree produced by SmaliParser#sField.
    def enterSField(self, ctx:SmaliParser.SFieldContext):
        pass

    # Exit a parse tree produced by SmaliParser#sField.
    def exitSField(self, ctx:SmaliParser.SFieldContext):
        pass


    # Enter a parse tree produced by SmaliParser#sAccList.
    def enterSAccList(self, ctx:SmaliParser.SAccListContext):
        pass

    # Exit a parse tree produced by SmaliParser#sAccList.
    def exitSAccList(self, ctx:SmaliParser.SAccListContext):
        pass


    # Enter a parse tree produced by SmaliParser#sAnnotation.
    def enterSAnnotation(self, ctx:SmaliParser.SAnnotationContext):
        pass

    # Exit a parse tree produced by SmaliParser#sAnnotation.
    def exitSAnnotation(self, ctx:SmaliParser.SAnnotationContext):
        pass


    # Enter a parse tree produced by SmaliParser#sSubannotation.
    def enterSSubannotation(self, ctx:SmaliParser.SSubannotationContext):
        pass

    # Exit a parse tree produced by SmaliParser#sSubannotation.
    def exitSSubannotation(self, ctx:SmaliParser.SSubannotationContext):
        pass


    # Enter a parse tree produced by SmaliParser#sParameter.
    def enterSParameter(self, ctx:SmaliParser.SParameterContext):
        pass

    # Exit a parse tree produced by SmaliParser#sParameter.
    def exitSParameter(self, ctx:SmaliParser.SParameterContext):
        pass


    # Enter a parse tree produced by SmaliParser#sAnnotationKeyName.
    def enterSAnnotationKeyName(self, ctx:SmaliParser.SAnnotationKeyNameContext):
        pass

    # Exit a parse tree produced by SmaliParser#sAnnotationKeyName.
    def exitSAnnotationKeyName(self, ctx:SmaliParser.SAnnotationKeyNameContext):
        pass


    # Enter a parse tree produced by SmaliParser#sAnnotationValue.
    def enterSAnnotationValue(self, ctx:SmaliParser.SAnnotationValueContext):
        pass

    # Exit a parse tree produced by SmaliParser#sAnnotationValue.
    def exitSAnnotationValue(self, ctx:SmaliParser.SAnnotationValueContext):
        pass


    # Enter a parse tree produced by SmaliParser#sBaseValue.
    def enterSBaseValue(self, ctx:SmaliParser.SBaseValueContext):
        pass

    # Exit a parse tree produced by SmaliParser#sBaseValue.
    def exitSBaseValue(self, ctx:SmaliParser.SBaseValueContext):
        pass


    # Enter a parse tree produced by SmaliParser#sArrayValue.
    def enterSArrayValue(self, ctx:SmaliParser.SArrayValueContext):
        pass

    # Exit a parse tree produced by SmaliParser#sArrayValue.
    def exitSArrayValue(self, ctx:SmaliParser.SArrayValueContext):
        pass


    # Enter a parse tree produced by SmaliParser#sInstruction.
    def enterSInstruction(self, ctx:SmaliParser.SInstructionContext):
        pass

    # Exit a parse tree produced by SmaliParser#sInstruction.
    def exitSInstruction(self, ctx:SmaliParser.SInstructionContext):
        pass


    # Enter a parse tree produced by SmaliParser#fline.
    def enterFline(self, ctx:SmaliParser.FlineContext):
        pass

    # Exit a parse tree produced by SmaliParser#fline.
    def exitFline(self, ctx:SmaliParser.FlineContext):
        pass


    # Enter a parse tree produced by SmaliParser#flocal.
    def enterFlocal(self, ctx:SmaliParser.FlocalContext):
        pass

    # Exit a parse tree produced by SmaliParser#flocal.
    def exitFlocal(self, ctx:SmaliParser.FlocalContext):
        pass


    # Enter a parse tree produced by SmaliParser#fend.
    def enterFend(self, ctx:SmaliParser.FendContext):
        pass

    # Exit a parse tree produced by SmaliParser#fend.
    def exitFend(self, ctx:SmaliParser.FendContext):
        pass


    # Enter a parse tree produced by SmaliParser#frestart.
    def enterFrestart(self, ctx:SmaliParser.FrestartContext):
        pass

    # Exit a parse tree produced by SmaliParser#frestart.
    def exitFrestart(self, ctx:SmaliParser.FrestartContext):
        pass


    # Enter a parse tree produced by SmaliParser#fprologue.
    def enterFprologue(self, ctx:SmaliParser.FprologueContext):
        pass

    # Exit a parse tree produced by SmaliParser#fprologue.
    def exitFprologue(self, ctx:SmaliParser.FprologueContext):
        pass


    # Enter a parse tree produced by SmaliParser#fepiogue.
    def enterFepiogue(self, ctx:SmaliParser.FepiogueContext):
        pass

    # Exit a parse tree produced by SmaliParser#fepiogue.
    def exitFepiogue(self, ctx:SmaliParser.FepiogueContext):
        pass


    # Enter a parse tree produced by SmaliParser#fregisters.
    def enterFregisters(self, ctx:SmaliParser.FregistersContext):
        pass

    # Exit a parse tree produced by SmaliParser#fregisters.
    def exitFregisters(self, ctx:SmaliParser.FregistersContext):
        pass


    # Enter a parse tree produced by SmaliParser#flocals.
    def enterFlocals(self, ctx:SmaliParser.FlocalsContext):
        pass

    # Exit a parse tree produced by SmaliParser#flocals.
    def exitFlocals(self, ctx:SmaliParser.FlocalsContext):
        pass


    # Enter a parse tree produced by SmaliParser#fcache.
    def enterFcache(self, ctx:SmaliParser.FcacheContext):
        pass

    # Exit a parse tree produced by SmaliParser#fcache.
    def exitFcache(self, ctx:SmaliParser.FcacheContext):
        pass


    # Enter a parse tree produced by SmaliParser#fcacheall.
    def enterFcacheall(self, ctx:SmaliParser.FcacheallContext):
        pass

    # Exit a parse tree produced by SmaliParser#fcacheall.
    def exitFcacheall(self, ctx:SmaliParser.FcacheallContext):
        pass


    # Enter a parse tree produced by SmaliParser#sLabel.
    def enterSLabel(self, ctx:SmaliParser.SLabelContext):
        pass

    # Exit a parse tree produced by SmaliParser#sLabel.
    def exitSLabel(self, ctx:SmaliParser.SLabelContext):
        pass


    # Enter a parse tree produced by SmaliParser#fpackageswitch.
    def enterFpackageswitch(self, ctx:SmaliParser.FpackageswitchContext):
        pass

    # Exit a parse tree produced by SmaliParser#fpackageswitch.
    def exitFpackageswitch(self, ctx:SmaliParser.FpackageswitchContext):
        pass


    # Enter a parse tree produced by SmaliParser#fspareswitch.
    def enterFspareswitch(self, ctx:SmaliParser.FspareswitchContext):
        pass

    # Exit a parse tree produced by SmaliParser#fspareswitch.
    def exitFspareswitch(self, ctx:SmaliParser.FspareswitchContext):
        pass


    # Enter a parse tree produced by SmaliParser#farraydata.
    def enterFarraydata(self, ctx:SmaliParser.FarraydataContext):
        pass

    # Exit a parse tree produced by SmaliParser#farraydata.
    def exitFarraydata(self, ctx:SmaliParser.FarraydataContext):
        pass


    # Enter a parse tree produced by SmaliParser#f0x.
    def enterF0x(self, ctx:SmaliParser.F0xContext):
        pass

    # Exit a parse tree produced by SmaliParser#f0x.
    def exitF0x(self, ctx:SmaliParser.F0xContext):
        pass


    # Enter a parse tree produced by SmaliParser#f0t.
    def enterF0t(self, ctx:SmaliParser.F0tContext):
        pass

    # Exit a parse tree produced by SmaliParser#f0t.
    def exitF0t(self, ctx:SmaliParser.F0tContext):
        pass


    # Enter a parse tree produced by SmaliParser#f1x.
    def enterF1x(self, ctx:SmaliParser.F1xContext):
        pass

    # Exit a parse tree produced by SmaliParser#f1x.
    def exitF1x(self, ctx:SmaliParser.F1xContext):
        pass


    # Enter a parse tree produced by SmaliParser#fconst.
    def enterFconst(self, ctx:SmaliParser.FconstContext):
        pass

    # Exit a parse tree produced by SmaliParser#fconst.
    def exitFconst(self, ctx:SmaliParser.FconstContext):
        pass


    # Enter a parse tree produced by SmaliParser#ff1c.
    def enterFf1c(self, ctx:SmaliParser.Ff1cContext):
        pass

    # Exit a parse tree produced by SmaliParser#ff1c.
    def exitFf1c(self, ctx:SmaliParser.Ff1cContext):
        pass


    # Enter a parse tree produced by SmaliParser#ft2c.
    def enterFt2c(self, ctx:SmaliParser.Ft2cContext):
        pass

    # Exit a parse tree produced by SmaliParser#ft2c.
    def exitFt2c(self, ctx:SmaliParser.Ft2cContext):
        pass


    # Enter a parse tree produced by SmaliParser#ff2c.
    def enterFf2c(self, ctx:SmaliParser.Ff2cContext):
        pass

    # Exit a parse tree produced by SmaliParser#ff2c.
    def exitFf2c(self, ctx:SmaliParser.Ff2cContext):
        pass


    # Enter a parse tree produced by SmaliParser#f2x.
    def enterF2x(self, ctx:SmaliParser.F2xContext):
        pass

    # Exit a parse tree produced by SmaliParser#f2x.
    def exitF2x(self, ctx:SmaliParser.F2xContext):
        pass


    # Enter a parse tree produced by SmaliParser#f3x.
    def enterF3x(self, ctx:SmaliParser.F3xContext):
        pass

    # Exit a parse tree produced by SmaliParser#f3x.
    def exitF3x(self, ctx:SmaliParser.F3xContext):
        pass


    # Enter a parse tree produced by SmaliParser#ft5c.
    def enterFt5c(self, ctx:SmaliParser.Ft5cContext):
        pass

    # Exit a parse tree produced by SmaliParser#ft5c.
    def exitFt5c(self, ctx:SmaliParser.Ft5cContext):
        pass


    # Enter a parse tree produced by SmaliParser#fm5c.
    def enterFm5c(self, ctx:SmaliParser.Fm5cContext):
        pass

    # Exit a parse tree produced by SmaliParser#fm5c.
    def exitFm5c(self, ctx:SmaliParser.Fm5cContext):
        pass


    # Enter a parse tree produced by SmaliParser#fmrc.
    def enterFmrc(self, ctx:SmaliParser.FmrcContext):
        pass

    # Exit a parse tree produced by SmaliParser#fmrc.
    def exitFmrc(self, ctx:SmaliParser.FmrcContext):
        pass


    # Enter a parse tree produced by SmaliParser#fm45cc.
    def enterFm45cc(self, ctx:SmaliParser.Fm45ccContext):
        pass

    # Exit a parse tree produced by SmaliParser#fm45cc.
    def exitFm45cc(self, ctx:SmaliParser.Fm45ccContext):
        pass


    # Enter a parse tree produced by SmaliParser#fm4rcc.
    def enterFm4rcc(self, ctx:SmaliParser.Fm4rccContext):
        pass

    # Exit a parse tree produced by SmaliParser#fm4rcc.
    def exitFm4rcc(self, ctx:SmaliParser.Fm4rccContext):
        pass


    # Enter a parse tree produced by SmaliParser#fmcustomc.
    def enterFmcustomc(self, ctx:SmaliParser.FmcustomcContext):
        pass

    # Exit a parse tree produced by SmaliParser#fmcustomc.
    def exitFmcustomc(self, ctx:SmaliParser.FmcustomcContext):
        pass


    # Enter a parse tree produced by SmaliParser#fmcustomrc.
    def enterFmcustomrc(self, ctx:SmaliParser.FmcustomrcContext):
        pass

    # Exit a parse tree produced by SmaliParser#fmcustomrc.
    def exitFmcustomrc(self, ctx:SmaliParser.FmcustomrcContext):
        pass


    # Enter a parse tree produced by SmaliParser#ftrc.
    def enterFtrc(self, ctx:SmaliParser.FtrcContext):
        pass

    # Exit a parse tree produced by SmaliParser#ftrc.
    def exitFtrc(self, ctx:SmaliParser.FtrcContext):
        pass


    # Enter a parse tree produced by SmaliParser#f31t.
    def enterF31t(self, ctx:SmaliParser.F31tContext):
        pass

    # Exit a parse tree produced by SmaliParser#f31t.
    def exitF31t(self, ctx:SmaliParser.F31tContext):
        pass


    # Enter a parse tree produced by SmaliParser#f1t.
    def enterF1t(self, ctx:SmaliParser.F1tContext):
        pass

    # Exit a parse tree produced by SmaliParser#f1t.
    def exitF1t(self, ctx:SmaliParser.F1tContext):
        pass


    # Enter a parse tree produced by SmaliParser#f2t.
    def enterF2t(self, ctx:SmaliParser.F2tContext):
        pass

    # Exit a parse tree produced by SmaliParser#f2t.
    def exitF2t(self, ctx:SmaliParser.F2tContext):
        pass


    # Enter a parse tree produced by SmaliParser#f2sb.
    def enterF2sb(self, ctx:SmaliParser.F2sbContext):
        pass

    # Exit a parse tree produced by SmaliParser#f2sb.
    def exitF2sb(self, ctx:SmaliParser.F2sbContext):
        pass


