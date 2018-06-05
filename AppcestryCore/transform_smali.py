#!/usr/bin/env python3


import argparse
import os
from antlr4 import *
from SmaliLexer import SmaliLexer
from SmaliListener import SmaliListener
from SmaliParser import SmaliParser
import inspect
import re


class SmaliTransformer(SmaliListener):
    MethodProtoDelimitersRe = "\(|\)|->|:"
    DataTypeSigns = ["L", "[", "B", "Z", "S", "C", "I", "F", "J", "D"]
    TrackedClassesPrefix = ["Landroid/", "android/", "Ljava/", "java/", "Ldalvik/", "dalvik/", "Lcom/google/",
                            "com/google/"]
    TrackedClassExceptionPrefix = ["Ljava/lang/Object", "java/lang/Object"]

    def __init__(self):
        # self.lines = []
        self.outputFileHandler = None
        self.parentedClassTracked = False

    def addCodeLine(self, line):
        self.outputFileHandler.write(line)
        self.outputFileHandler.write("\n")

    def getAttributeExistence(self, ctx, attrList):
        ouputString = ""
        effectiveAttributes = dir(ctx)
        for p in attrList:
            if p in effectiveAttributes:
                argSpec = inspect.getfullargspec(getattr(ctx, p))
                if len(argSpec.args) > 1:
                    i = 0
                    while getattr(ctx, p)(i) is not None:
                        i = i + 1
                    if i <= 0:
                        continue
                    ouputString = " ".join([ouputString, "{}_x{}".format(p, i)])
                elif getattr(ctx, p)() is not None:
                    ouputString = " ".join([ouputString, p])

        return ouputString

    def isClassTracked(self, objectName):
        for prefix in SmaliTransformer.TrackedClassesPrefix:
            if objectName.startswith(prefix):
                if objectName not in SmaliTransformer.TrackedClassExceptionPrefix:
                    return True
        return False

    def filterNonSystemObjectNames(self, objectString):
        if objectString.startswith("L"):
            objectName = objectString[1:]
            if not self.isClassTracked(objectName):
                return "L[objectLevel{}]".format(objectName.count("/"))
        return objectString

    def getTransformedParameterTypes(self, typeString):
        expectingPrimitiveTypeSign = True
        objStringBuffer = ""
        resultArr = []

        for c in typeString:

            if not expectingPrimitiveTypeSign:
                if c == ";":
                    expectingPrimitiveTypeSign = True
                    resultArr.append(objStringBuffer)
                    objStringBuffer = ""
                    continue
                else:
                    objStringBuffer = "{}{}".format(objStringBuffer, c)

            if expectingPrimitiveTypeSign:
                if c == "L":
                    expectingPrimitiveTypeSign = False
                    objStringBuffer = "L"
                else:
                    resultArr.append(c)

        resultArr = [self.filterNonSystemObjectNames(r) for r in resultArr]

        return resultArr

    def tryGetAttributeText(self, ctx, attribute, index: int = None):
        resultText = ""
        if index is None:
            if "getText" in dir(getattr(ctx, attribute)()):
                resultText = getattr(ctx, attribute)().getText()
            else:
                resultText = getattr(ctx, attribute)()
        else:
            if "getText" in dir(getattr(ctx, attribute)(index)):
                resultText = getattr(ctx, attribute)(index).getText()
            else:
                resultText = getattr(ctx, attribute)(index)

        if attribute == "REGISTER":
            return resultText[0]
        if attribute == "LABEL":
            return resultText[1:].split("_")[0]
        elif attribute in ["METHOD_PART", "METHOD_FULL", "FIELD_FULL", "FIELD_PART", "OBJECT_TYPE"]:
            segments = re.split(SmaliTransformer.MethodProtoDelimitersRe, resultText)
            # pprint(segments)

            if attribute == "METHOD_PART":
                methodName = segments[0]
                methodArguments = self.getTransformedParameterTypes(segments[1])
                methodReturns = self.getTransformedParameterTypes(segments[2])
                resultText = " methodArgs_{} methodReturns_{}".format(",".join(methodArguments),
                                                                      ",".join(methodReturns))
                if self.parentedClassTracked:
                    resultText = " methodName_{}{}".format(methodName, resultText)
            elif attribute == "METHOD_FULL":
                objectName = self.getTransformedParameterTypes(segments[0])
                methodName = segments[1]
                methodArguments = self.getTransformedParameterTypes(segments[2])
                methodReturns = self.getTransformedParameterTypes(segments[3])
                resultText = " objectName_{} methodArgs_{} methodReturns_{}".format("".join(objectName),
                                                                                    ",".join(methodArguments),
                                                                                    ",".join(methodReturns))
                if self.isClassTracked("".join(objectName)):
                    resultText = " methodName_{}{}".format(methodName, resultText)
            elif attribute == "FIELD_PART":
                fieldType = self.getTransformedParameterTypes(segments[1])
                resultText = " fieldType_{}".format("".join(fieldType))
            elif attribute == "FIELD_FULL":
                fieldObject = self.getTransformedParameterTypes(segments[0])
                fieldType = self.getTransformedParameterTypes(segments[2])
                resultText = " fieldObject_{} fieldType_{}".format("".join(fieldObject), "".join(fieldType))
            elif attribute == "OBJECT_TYPE":
                resultText = " objectType_{}".format("".join(self.getTransformedParameterTypes(segments[0])))

        return resultText

    def getAttributeValues(self, ctx, attrList):
        ouputString = ""
        effectiveAttributes = dir(ctx)
        for p in attrList:
            if p in effectiveAttributes:
                argSpec = inspect.getfullargspec(getattr(ctx, p))
                if len(argSpec.args) > 1:
                    i = 0
                    while getattr(ctx, p)(i) is not None:
                        ouputString = "{} {}_{}:{}".format(ouputString, p, i, self.tryGetAttributeText(ctx, p, i))
                        i = i + 1
                else:
                    if getattr(ctx, p)() is not None:
                        ouputString = "{} {}:{}".format(ouputString, p, self.tryGetAttributeText(ctx, p))
        return ouputString

    def enterSFile(self, ctx: SmaliParser.SFileContext):
        self.addCodeLine(" ".join([".class",
                                   self.getAttributeValues(ctx, ["sAccList", "OBJECT_TYPE"])
                                   ]))

    def enterSSuper(self, ctx: SmaliParser.SSuperContext):
        self.parentedClassTracked = self.isClassTracked(ctx.OBJECT_TYPE().getText())
        self.addCodeLine(" ".join([".super",
                                   self.getAttributeValues(ctx, ["OBJECT_TYPE"])
                                   ]))

    def enterSInterface(self, ctx: SmaliParser.SInterfaceContext):
        self.parentedClassTracked = self.isClassTracked(ctx.OBJECT_TYPE().getText())
        self.addCodeLine(" ".join([".implements",
                                   self.getAttributeValues(ctx, ["OBJECT_TYPE"])
                                   ]))

    def enterSAnnotation(self, ctx: SmaliParser.SAnnotationContext):
        self.addCodeLine(" ".join([".annotation",
                                   self.getAttributeValues(ctx, ["ANN_VISIBLE", "OBJECT_TYPE"])
                                   ]))

    def enterSAnnotationKeyName(self, ctx: SmaliParser.SAnnotationKeyNameContext):
        self.addCodeLine(" ".join([".sAnnotationKeyName",
                                   self.getAttributeValues(ctx, ["ID", "ANN_VISIBLE"]),
                                   self.getAttributeExistence(ctx,
                                                              ["PRIMITIVE_TYPE", "VOID_TYPE", "REGISTER", "BOOLEAN",
                                                               "NULL", "FLOAT_INFINITY", "DOUBLE_INFINITY",
                                                               "FLOAT_NAN", "DOUBLE_NAN", "NOP", "MOVE", "RETURN",
                                                               "CONST", "THROW", "GOTO", "AGET", "APUT", "IGET",
                                                               "IPUT", "SGET", "SPUT", "ACC"])
                                   ]))

    def enterSField(self, ctx: SmaliParser.SFieldContext):
        self.addCodeLine(" ".join([".field",
                                   self.getAttributeValues(ctx, ["sAccList", "FIELD_FULL", "FIELD_PART"])
                                   ]))

    def enterSMethod(self, ctx: SmaliParser.SMethodContext):
        self.addCodeLine(" ".join([".method",
                                   self.getAttributeValues(ctx, ["sAccList", "METHOD_FULL", "METHOD_PART"]),
                                   self.getAttributeExistence(ctx, ["sParameter"])
                                   ]))

    def enterFregisters(self, ctx: SmaliParser.FregistersContext):
        self.addCodeLine(" ".join([".registers",
                                   self.getAttributeExistence(ctx, ["INT"])
                                   ]))

    def enterFcache(self, ctx: SmaliParser.FcacheContext):
        self.addCodeLine(" ".join([".catch",
                                   self.getAttributeValues(ctx, ["OBJECT_TYPE"]),
                                   self.getAttributeExistence(ctx, ["LABEL"])
                                   ]))

    def enterFcacheall(self, ctx: SmaliParser.FcacheallContext):
        self.addCodeLine(" ".join([".catch-all",
                                   self.getAttributeExistence(ctx, ["LABEL"])
                                   ]))

    def enterFpackageswitch(self, ctx: SmaliParser.FpackageswitchContext):
        self.addCodeLine(" ".join([".packed-switch",
                                   self.getAttributeExistence(ctx, ["INT", "LABEL"])
                                   ]))

    def enterFspareswitch(self, ctx: SmaliParser.FspareswitchContext):
        self.addCodeLine(" ".join([".sparse-switch",
                                   self.getAttributeExistence(ctx, ["INT", "LABEL"])
                                   ]))

    def enterFarraydata(self, ctx: SmaliParser.FarraydataContext):
        self.addCodeLine(" ".join([".array-data",
                                   self.getAttributeExistence(ctx, ["INT"])
                                   ]))

    def enterF0x(self, ctx: SmaliParser.F0xContext):
        self.addCodeLine(ctx.op.text)

    def enterF0t(self, ctx: SmaliParser.F0tContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeExistence(ctx, ["LABEL", "GOTO"])
                                   ]))

    def enterF1x(self, ctx: SmaliParser.F1xContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["RETURN", "THROW"])
                                   ]))

    def enterFconst(self, ctx: SmaliParser.FconstContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["OBJECT_TYPE", "REGISTER"]),
                                   self.getAttributeExistence(ctx, ["CONST", "INT", "LONG", "STRING"
                                       , "ARRAY_TYPE"])
                                   ]))

    def enterFf1c(self, ctx: SmaliParser.Ff1cContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["FIELD_FULL", "REGISTER"]),
                                   self.getAttributeExistence(ctx, ["SGET", "SPUT"])
                                   ]))

    def enterFt2c(self, ctx: SmaliParser.Ft2cContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER", "OBJECT_TYPE", "ARRAY_TYPE"]),
                                   ]))

    def enterFf2c(self, ctx: SmaliParser.Ff2cContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["FIELD_FULL", "REGISTER"]),
                                   self.getAttributeExistence(ctx, ["IGET", "IPUT"])
                                   ]))

    def enterF2x(self, ctx: SmaliParser.F2xContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["MOVE", "REGISTER"])
                                   ]))

    def enterF3x(self, ctx: SmaliParser.F3xContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["AGET", "APUT"])
                                   ]))

    def enterFt5c(self, ctx: SmaliParser.Ft5cContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["ARRAY_TYPE", "REGISTER"]),
                                   ]))

    def enterFm5c(self, ctx: SmaliParser.Fm5cContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["METHOD_FULL", "REGISTER"])
                                   ]))

    def enterFmrc(self, ctx: SmaliParser.FmrcContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["METHOD_FULL", "REGISTER"])
                                   ]))

    def enterFm45cc(self, ctx: SmaliParser.Fm45ccContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["METHOD_FULL", "METHOD_PROTO", "REGISTER"])
                                   ]))

    def enterFm4rcc(self, ctx: SmaliParser.Fm4rccContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["METHOD_FULL", "METHOD_PROTO", "REGISTER"])
                                   ]))

    def enterFmcustomc(self, ctx: SmaliParser.FmcustomcContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["sArrayValue", "REGISTER"])
                                   ]))

    def enterFmcustomrc(self, ctx: SmaliParser.FmcustomrcContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["sArrayValue", "REGISTER"])
                                   ]))

    def enterFtrc(self, ctx: SmaliParser.FtrcContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["OBJECT_TYPE", "ARRAY_TYPE", "REGISTER"]),
                                   ]))

    def enterF31t(self, ctx: SmaliParser.F31tContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["LABEL"])
                                   ]))

    def enterF1t(self, ctx: SmaliParser.F1tContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["LABEL"])
                                   ]))

    def enterF2t(self, ctx: SmaliParser.F2tContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["LABEL"])
                                   ]))

    def enterF2sb(self, ctx: SmaliParser.F2sbContext):
        self.addCodeLine(" ".join([ctx.op.text,
                                   self.getAttributeValues(ctx, ["REGISTER"]),
                                   self.getAttributeExistence(ctx, ["INT"])
                                   ]))

    def enterSLabel(self, ctx: SmaliParser.SLabelContext):
        self.addCodeLine(" ".join(["label",
                                   self.getAttributeValues(ctx, ["LABEL"])
                                   ]))


def TransformMergedSmaliFile(inputFilename, outputFilename):

    lexer = SmaliLexer(FileStream(inputFilename, encoding="utf-8"))
    tokens = CommonTokenStream(lexer)
    parser = SmaliParser(tokens)
    tree = parser.sFiles()
    transformer = SmaliTransformer()
    transformer.outputFileHandler = open(outputFilename, "w")
    walker = ParseTreeWalker()
    walker.walk(transformer, tree)
    # outputFile.write("\r\n".join(transformer.lines))
    transformer.outputFileHandler.close()


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--inputFile", help="The source Smali file", required=True)
    argParser.add_argument("--outputFile", help="The output file to be saved", required=True)
    args = argParser.parse_args()

    inputFilename = os.path.realpath(args.inputFile)
    outputFilename = os.path.realpath(args.outputFile)
    TransformMergedSmaliFile(inputFilename, outputFilename)
