from dataclasses import dataclass
from typing import ClassVar, Dict, List
from enum import Enum, auto
from symbolTranslator import *
import re

class TokenType(Enum):
    OPERATOR = auto()
    OPENING_BRACKET = auto()
    CLOSING_BRACKET = auto()
    FUNCTION = auto()
    TERM = auto()
    COMMA = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str

    def __str__(self):
        return f"Type: {self.type}, Value: {self.value}"

@dataclass(frozen=True)
class SymbolInfo:
    translation: str | None
    precedence: int
    arity: int = 2

class SymbolSet:
    OPERATORS: ClassVar[Dict[str, SymbolInfo]] = {
        # Assignment (lowest binding in machine expressions)
        "≔": SymbolInfo(None, 1, 2),

        # Quantifiers
        "∀": SymbolInfo(None, 2, 2),
        "∃": SymbolInfo(None, 2, 2),
        "∃!": SymbolInfo(None, 2, 2),
        "∄": SymbolInfo(None, 2, 2),

        # Implication
        "⇒": SymbolInfo(None, 3, 2),

        # Logical OR
        "∨": SymbolInfo(None, 4, 2),

        # Logical AND
        "∧": SymbolInfo(None, 5, 2),

        # Relations
        "=": SymbolInfo(None, 6, 2),
        "≠": SymbolInfo(None, 6, 2),
        "<": SymbolInfo(None, 6, 2),
        ">": SymbolInfo(None, 6, 2),
        "≤": SymbolInfo(None, 6, 2),
        "≥": SymbolInfo(None, 6, 2),
        "∈": SymbolInfo(None, 6, 2),
        "∉": SymbolInfo(None, 6, 2),
        "⊆": SymbolInfo(None, 6, 2),
        "⊂": SymbolInfo(None, 6, 2),
        "⊇": SymbolInfo(None, 6, 2),
        "⊃": SymbolInfo(None, 6, 2),

        # Set operators
        "∪": SymbolInfo(None, 7, 2),
        "∩": SymbolInfo(None, 7, 2),
        "∖": SymbolInfo(None, 7, 2),

        # Range
        "‥": SymbolInfo(None, 8, 2),

        # Additive
        "+": SymbolInfo(None, 9, 2),
        "-": SymbolInfo(None, 9, 2),
        "−": SymbolInfo(None, 9, 2),

        # Multiplicative
        "*": SymbolInfo(None, 10, 2),
        "/": SymbolInfo(None, 10, 2),
        "mod": SymbolInfo(None, 10, 2),
        "·": SymbolInfo(None, 10, 2),

        # Unary NOT (highest among logical)
        "¬": SymbolInfo(None, 11, 1),

        # Parentheses / structural
        "(": SymbolInfo(None, 0, 0),
        ")": SymbolInfo(None, 0, 0),
        "{": SymbolInfo(None, 0, 0),
        "}": SymbolInfo(None, 0, 0),
        "[": SymbolInfo(None, 0, 0),
        "]": SymbolInfo(None, 0, 0),
        ",": SymbolInfo(None, 0, 0),
    }

    def precedence(self, op: str) -> int:
        return self.OPERATORS.get(op, SymbolInfo(op, -1)).precedence

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

            elif (i + 1 < len(tokens) and tokens[i + 1] == "("): # must add certain specialised strings like parity, card, etc. here as well
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
    
    def translate(self, expr: str, purpose: TranslationPurpose = None) -> str:
        tokens = self.classify_tokens(expr)
        postfix_tokens = self.to_postfix(tokens)
        stack: List[str] = []
        output = []

        handlers: Dict[str, TranslationHandler] = {
            "partition": PartitionTranslation(),
            "=": EqualityTranslation(),
            ">": GreaterTranslation(),
            "<": LessTranslation(),
            "≥": GreaterEqualTranslation(),
            "≤": LessEqualTranslation(),
            "≔": AssignmentTranslation(),
            "+": PlusTranslation(),
            "-": MinusTranslation(),
            "/": DivideTranslation(),
            "*": MultiplyTranslation(),
        }

        for token in postfix_tokens:
            # print(f"Processing token: {token}, Stack before: {stack}")
            if token.type == TokenType.TERM:
                value = token.value if token.value not in ("TRUE", "FALSE") else token.value.lower()
                stack.append(value)

            elif token.type in (TokenType.OPERATOR, TokenType.FUNCTION):
                handler = handlers.get(token.value)
                if handler:
                    stack.append(handler.translate(stack, purpose=purpose))

        if len(stack) != 1:
            raise ValueError("Invalid expression, stack should have exactly one element at the end of translation.")
        
        return "".join(stack).strip()