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

        handlers: Dict[str, TranslationHandler] = {
            "partition": PartitionTranslation(), # Do one for parity. parity is both a term and a function it seems...
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
        }

        print(f"Translating expression: {expr}")        
        for token in postfix_tokens:
            print(f"     Processing token: {token}, Stack before processing: {stack}")
            if token.type == TokenType.TERM:
                value = token.value if token.value not in ("TRUE", "FALSE") else token.value.lower()
                stack.append(value)

            elif token.type in (TokenType.OPERATOR, TokenType.FUNCTION):
                handler = handlers.get(token.value)
                if handler:
                    result = handler.translate(stack, purpose)
                    stack.append(result)
                else:
                    raise ValueError(f"No translation handler for operator/function: {token.value}")
        if len(stack) != 1:
            raise ValueError("Invalid expression, stack should have exactly one element at the end of translation.")
        print(f"Final translated expression: {stack[0].replace("\n", " [EOL] ")}\n")
        return "".join(stack).strip()