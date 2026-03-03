from dataclasses import dataclass
from typing import ClassVar, Dict, List, Tuple, Set
from enum import Enum, auto
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

class SymbolSet:
    OPERATORS: ClassVar[Dict[str, SymbolInfo]] = {
        "¬": SymbolInfo(None, 9),
        "‥": SymbolInfo(None, 9),
        "∀": SymbolInfo(None, 1),
        "∃": SymbolInfo(None, 1),
        "∃!": SymbolInfo(None, 1),
        "∄": SymbolInfo(None, 1),
        "⇒": SymbolInfo(None, 2),
        "=": SymbolInfo(None, 3),
        "≠": SymbolInfo(None, 3),
        "<": SymbolInfo(None, 3),
        ">": SymbolInfo(None, 3),
        "≤": SymbolInfo(None, 3),
        "≥": SymbolInfo(None, 3),
        "∈": SymbolInfo(None, 3),
        "∉": SymbolInfo(None, 3),
        "⊆": SymbolInfo(None, 3),
        "⊂": SymbolInfo(None, 3),
        "⊇": SymbolInfo(None, 3),
        "⊃": SymbolInfo(None, 3),
        "∨": SymbolInfo(None, 4),
        "∪": SymbolInfo(None, 4),
        "∧": SymbolInfo(None, 5),
        "∩": SymbolInfo(None, 5),
        "∖": SymbolInfo(None, 6),
        "+": SymbolInfo(None, 7),
        "-": SymbolInfo(None, 7),
        "−": SymbolInfo(None, 7),
        "*": SymbolInfo(None, 8),
        "/": SymbolInfo(None, 8),
        "mod": SymbolInfo(None, 8),
        "·": SymbolInfo(None, 8),
        "(": SymbolInfo(None, 0),
        ")": SymbolInfo(None, 0),
        "{": SymbolInfo(None, 0),
        "}": SymbolInfo(None, 0),
        "[": SymbolInfo(None, 0),
        "]": SymbolInfo(None, 0),
        ",": SymbolInfo(None, 0),
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
        print(f"Regex split result: {reg_pattern}")
        tokens =  [t.strip() for t in reg_pattern if t.strip()]
        classified = []
        for i, token in enumerate(tokens):
            print(f"Processing token: '{token}'")
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