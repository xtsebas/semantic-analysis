# Generated from Compiscript.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .CompiscriptParser import CompiscriptParser
else:
    from CompiscriptParser import CompiscriptParser

# This class defines a complete generic visitor for a parse tree produced by CompiscriptParser.

class CompiscriptVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by CompiscriptParser#program.
    def visitProgram(self, ctx:CompiscriptParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#statement.
    def visitStatement(self, ctx:CompiscriptParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#block.
    def visitBlock(self, ctx:CompiscriptParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:CompiscriptParser.VariableDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#constantDeclaration.
    def visitConstantDeclaration(self, ctx:CompiscriptParser.ConstantDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#typeAnnotation.
    def visitTypeAnnotation(self, ctx:CompiscriptParser.TypeAnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#initializer.
    def visitInitializer(self, ctx:CompiscriptParser.InitializerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#assignment.
    def visitAssignment(self, ctx:CompiscriptParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#expressionStatement.
    def visitExpressionStatement(self, ctx:CompiscriptParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#printStatement.
    def visitPrintStatement(self, ctx:CompiscriptParser.PrintStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ifStatement.
    def visitIfStatement(self, ctx:CompiscriptParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#whileStatement.
    def visitWhileStatement(self, ctx:CompiscriptParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:CompiscriptParser.DoWhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#forStatement.
    def visitForStatement(self, ctx:CompiscriptParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#foreachStatement.
    def visitForeachStatement(self, ctx:CompiscriptParser.ForeachStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#breakStatement.
    def visitBreakStatement(self, ctx:CompiscriptParser.BreakStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#continueStatement.
    def visitContinueStatement(self, ctx:CompiscriptParser.ContinueStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#returnStatement.
    def visitReturnStatement(self, ctx:CompiscriptParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#tryCatchStatement.
    def visitTryCatchStatement(self, ctx:CompiscriptParser.TryCatchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#switchStatement.
    def visitSwitchStatement(self, ctx:CompiscriptParser.SwitchStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#switchCase.
    def visitSwitchCase(self, ctx:CompiscriptParser.SwitchCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#defaultCase.
    def visitDefaultCase(self, ctx:CompiscriptParser.DefaultCaseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#functionDeclaration.
    def visitFunctionDeclaration(self, ctx:CompiscriptParser.FunctionDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameters.
    def visitParameters(self, ctx:CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#parameter.
    def visitParameter(self, ctx:CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CompiscriptParser.ClassDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#classMember.
    def visitClassMember(self, ctx:CompiscriptParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#expression.
    def visitExpression(self, ctx:CompiscriptParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#AssignExpr.
    def visitAssignExpr(self, ctx:CompiscriptParser.AssignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#PropertyAssignExpr.
    def visitPropertyAssignExpr(self, ctx:CompiscriptParser.PropertyAssignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ExprNoAssign.
    def visitExprNoAssign(self, ctx:CompiscriptParser.ExprNoAssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#TernaryExpr.
    def visitTernaryExpr(self, ctx:CompiscriptParser.TernaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LogicalOrPassthrough.
    def visitLogicalOrPassthrough(self, ctx:CompiscriptParser.LogicalOrPassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LogicalOrOp.
    def visitLogicalOrOp(self, ctx:CompiscriptParser.LogicalOrOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LogicalAndPassthrough.
    def visitLogicalAndPassthrough(self, ctx:CompiscriptParser.LogicalAndPassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LogicalAndOp.
    def visitLogicalAndOp(self, ctx:CompiscriptParser.LogicalAndOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#EqualityPassthrough.
    def visitEqualityPassthrough(self, ctx:CompiscriptParser.EqualityPassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#EqualityOp.
    def visitEqualityOp(self, ctx:CompiscriptParser.EqualityOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#RelationalPassthrough.
    def visitRelationalPassthrough(self, ctx:CompiscriptParser.RelationalPassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#RelationalOp.
    def visitRelationalOp(self, ctx:CompiscriptParser.RelationalOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#AdditiveOp.
    def visitAdditiveOp(self, ctx:CompiscriptParser.AdditiveOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#AdditivePassthrough.
    def visitAdditivePassthrough(self, ctx:CompiscriptParser.AdditivePassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#MultiplicativePassthrough.
    def visitMultiplicativePassthrough(self, ctx:CompiscriptParser.MultiplicativePassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#MultiplicativeOp.
    def visitMultiplicativeOp(self, ctx:CompiscriptParser.MultiplicativeOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#UnaryOp.
    def visitUnaryOp(self, ctx:CompiscriptParser.UnaryOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#UnaryPassthrough.
    def visitUnaryPassthrough(self, ctx:CompiscriptParser.UnaryPassthroughContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LiteralPrimary.
    def visitLiteralPrimary(self, ctx:CompiscriptParser.LiteralPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#LeftHandSidePrimary.
    def visitLeftHandSidePrimary(self, ctx:CompiscriptParser.LeftHandSidePrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ParenthesizedExpr.
    def visitParenthesizedExpr(self, ctx:CompiscriptParser.ParenthesizedExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#literalExpr.
    def visitLiteralExpr(self, ctx:CompiscriptParser.LiteralExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#leftHandSide.
    def visitLeftHandSide(self, ctx:CompiscriptParser.LeftHandSideContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:CompiscriptParser.IdentifierExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#NewExpr.
    def visitNewExpr(self, ctx:CompiscriptParser.NewExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#ThisExpr.
    def visitThisExpr(self, ctx:CompiscriptParser.ThisExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#CallExpr.
    def visitCallExpr(self, ctx:CompiscriptParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#IndexExpr.
    def visitIndexExpr(self, ctx:CompiscriptParser.IndexExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#PropertyAccessExpr.
    def visitPropertyAccessExpr(self, ctx:CompiscriptParser.PropertyAccessExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#arguments.
    def visitArguments(self, ctx:CompiscriptParser.ArgumentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#arrayLiteral.
    def visitArrayLiteral(self, ctx:CompiscriptParser.ArrayLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#type.
    def visitType(self, ctx:CompiscriptParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CompiscriptParser#baseType.
    def visitBaseType(self, ctx:CompiscriptParser.BaseTypeContext):
        return self.visitChildren(ctx)



del CompiscriptParser