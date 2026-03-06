from dataclasses import dataclass
from typing import ClassVar, Dict, List
from symbolTranslator import *
from components import Token, TokenType
import re

@dataclass(frozen=True)
class SymbolInfo:
    precedence: int
    
class SymbolSet:
    OPERATORS: ClassVar[Dict[str, SymbolInfo]] = {
        # Assignment (lowest binding in machine expressions)
        "≔": SymbolInfo(1),

        # Quantifiers
        "∀": SymbolInfo(2),
        "∃": SymbolInfo(2),
        "∃!": SymbolInfo(2),
        "∄": SymbolInfo(2),

        # Implication
        "⇒": SymbolInfo(3),

        # Logical OR
        "∨": SymbolInfo(4),

        # Logical AND
        "∧": SymbolInfo(5),

        # Relations
        "=": SymbolInfo(6),
        "≠": SymbolInfo(6),
        "<": SymbolInfo(6),
        ">": SymbolInfo(6),
        "≤": SymbolInfo(6),
        "≥": SymbolInfo(6),
        "∈": SymbolInfo(6),
        "∉": SymbolInfo(6),
        "⊆": SymbolInfo(6),
        "⊂": SymbolInfo(6),
        "⊇": SymbolInfo(6),
        "⊃": SymbolInfo(6),

        "→" : SymbolInfo(6.5),  # Function type, treated as relation for precedence

        # Set operators
        "∪": SymbolInfo(7),
        "∩": SymbolInfo(7),
        "∖": SymbolInfo(7),

        # Range
        "‥": SymbolInfo(8),

        # Additive
        "+": SymbolInfo(9),
        "-": SymbolInfo(9),
        "−": SymbolInfo(9),

        # Multiplicative
        "*": SymbolInfo(10),
        "/": SymbolInfo(10),
        "mod": SymbolInfo(10),
        "·": SymbolInfo(10),

        # Unary NOT (highest among logical)
        "¬": SymbolInfo(11),

        # Parentheses / structural
        "(": SymbolInfo(0),
        ")": SymbolInfo(0),
        "{": SymbolInfo(0),
        "}": SymbolInfo(0),
        "[": SymbolInfo(0),
        "]": SymbolInfo(0),
        ",": SymbolInfo(0),
    }

    def precedence(self, op: str) -> int:
        return self.OPERATORS.get(op, SymbolInfo(-1)).precedence

    def is_operator(self, s: str) -> bool:
        return s in self.OPERATORS
    
    
    def generate_regex_pattern(self) -> re.Pattern:
        symbols = sorted(self.OPERATORS, key=len, reverse=True)
        pattern = "|".join(re.escape(s) for s in symbols)
        return re.compile(f"({pattern})")

class SyntaxTranslator:
    IDENTIFIER_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    NUMBER_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[0-9]+$")
    sym_set: SymbolSet = SymbolSet()
    
    def __init__(self):
        self.TOKEN_PATTERN = self.sym_set.generate_regex_pattern()

    def classify_tokens(self, expr: str) -> List[Token]:
        reg_pattern = self.TOKEN_PATTERN.split(expr)
        tokens =  [t.strip() for t in reg_pattern if t.strip()]
        classified = []
        for i, token in enumerate(tokens):
            if self.sym_set.is_operator(token):
                if token == ",":
                    classified.append(Token(TokenType.COMMA, token))
                elif token == "(":
                    classified.append(Token(TokenType.OPENING_BRACKET, token))
                elif token == ")":
                    classified.append(Token(TokenType.CLOSING_BRACKET, token))
                elif token not in "][]}{":
                    classified.append(Token(TokenType.OPERATOR, token))

            elif (i + 1 < len(tokens) and tokens[i + 1] == "("):
                classified.append(Token(TokenType.FUNCTION, token))                

            else:
                classified.append(Token(TokenType.TERM, token))

        return classified   

    def to_postfix(self, tokens: List[Token]) -> List[Token]:
        output: List[Token] = []
        stack: List[Token] = []

        for token in tokens:
            match token.type:
                case TokenType.TERM:
                    output.append(token)
                case TokenType.FUNCTION:
                    stack.append(token)
                case TokenType.OPERATOR:
                    while (stack and stack[-1].type == TokenType.OPERATOR 
                           and self.sym_set.precedence(stack[-1].value) >= self.sym_set.precedence(token.value)):
                        output.append(stack.pop())
                    stack.append(token)
                case TokenType.OPENING_BRACKET:
                    stack.append(token)
                case TokenType.CLOSING_BRACKET:
                    while stack and stack[-1].type != TokenType.OPENING_BRACKET:
                        output.append(stack.pop())
                    if stack and stack[-1].type == TokenType.OPENING_BRACKET:
                        stack.pop()
                    if stack and stack[-1].type == TokenType.FUNCTION:
                        output.append(stack.pop())
        while stack:
            output.append(stack.pop())
        return output
    
    def translate(self, expr: str, context: TranslationContext = None) -> str:
        tokens = self.classify_tokens(expr)
        postfix_tokens = self.to_postfix(tokens)
        stack: List[Token] = []

        handlers: Dict[str, TranslationHandler] = {
            "partition": PartitionTranslation(),
            "=": EqualityTranslation(),
            ">": GreaterTranslation(),
            "<": LessTranslation(),
            "≥": GreaterEqualTranslation(),
            "≤": LessEqualTranslation(),
            "≔": AssignmentTranslation(),
            "+": PlusTranslation(),
            "−": MinusTranslation(),
            "/": DivideTranslation(),
            "*": MultiplyTranslation(),
            "⇒": ImplicationTranslation(),
            "∧": AndTranslation(),
            "∨": OrTranslation(),
            "¬": NotTranslation(),
            "∈": MembershipTranslation(),
            "→": FunctionTypeTranslation(),
        }

        print(f"Translating expression: {expr}")        
        for token in postfix_tokens:
            stack_values = [t.value for t in stack]
            print(f"     Processing token: {token}, Stack before processing: {stack_values}")
            if token.type == TokenType.TERM:
                value = token.value if token.value not in ("TRUE", "FALSE") else token.value.lower()
                stack.append(Token(TokenType.TRANSLATED, value))

            elif token.type in (TokenType.OPERATOR, TokenType.FUNCTION):
                handler = handlers.get(token.value)
                if handler:
                    handler.translate(stack, context)
                else:
                    raise ValueError(f"No translation handler for operator/function: {token.value}")
        if len(stack) != 1:
            raise ValueError("Invalid expression, stack should have exactly one element at the end of translation.")
        if stack[0].type != TokenType.TRANSLATED:
            raise ValueError("Invalid expression, final token should be of type TRANSLATED.")
        
        translation = stack[0].value
        print(f"Final translated expression: {translation.replace("\n", " [EOL] ")}\n")
        return "".join(translation).strip()