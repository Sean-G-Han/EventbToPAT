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

class SyntaxTranslator:

    # Event-B symbol → operation name
    OPERATORS: ClassVar[Dict[str, Tuple[str, int, int]]] = {
        # logical (PAT symbol, arity, precedence)
        "¬": ("!", 1, 5),
        "∧": ("&&", 2, 4),
        "∨": ("||", 2, 3),
        "⇒": ("=>", 2, 2),

        # comparison
        "=": ("==", 2, 6),
        "≠": ("!=", 2, 6),
        "<": ("<", 2, 6),
        ">": (">", 2, 6),
        "≤": ("<=", 2, 6),
        "≥": (">=", 2, 6),
        "∈": ("in", 2, 6),
        "∉": ("not in", 2, 6),
        "⊆": ("subseteq", 2, 6),
        "⊂": ("subset", 2, 6),
        "⊇": ("supseteq", 2, 6),
        "⊃": ("supset", 2, 6),

        # set operators
        "∪": ("union", 2, 7),
        "∩": ("intersect", 2, 7),
        "∖": ("setminus", 2, 7),

        # arithmetic
        "+": ("+", 2, 8),
        "-": ("-", 2, 8),
        "*": ("*", 2, 9),
        "/": ("/", 2, 9),
        "mod": ("mod", 2, 9),

        # brackets and comma (no precedence, arity = 0)
        "(": ("(", 0, 0),
        ")": (")", 0, 0),
        "{": ("{", 0, 0),
        "}": ("}", 0, 0),
        "[": ("[", 0, 0),
        "]": ("]", 0, 0),
        ",": (",", 0, 0),
    }

    FUNCTIONS: ClassVar[Set[str]] = set("partition")

    IDENTIFIER_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    NUMBER_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[0-9]+$")
    
    def __init__(self):
        self.TOKEN_PATTERN = self._build_token_pattern()

    @classmethod
    def _build_token_pattern(cls):
        symbols = sorted(cls.OPERATORS, key=len, reverse=True)
        pattern = "|".join(re.escape(s) for s in symbols)
        return re.compile(f"({pattern})")

    def classify_tokens(self, expr: str) -> List[Token]:
        reg_pattern = self.TOKEN_PATTERN.split(expr)
        tokens =  [t.strip() for t in reg_pattern if t.strip()]
        classified = []
        for i, token in enumerate(tokens):
            if token in self.OPERATORS:
                if token == ",":
                    classified.append(Token(TokenType.COMMA, token))
                elif token == "(":
                    classified.append(Token(TokenType.OPENING_BRACKET, token))
                elif token == ")":
                    classified.append(Token(TokenType.CLOSING_BRACKET, token))
                elif token not in "][]}{":
                    classified.append(Token(TokenType.OPERATOR, token))

            elif (
                (token in self.FUNCTIONS or self.IDENTIFIER_PATTERN.match(token))
                and i + 1 < len(tokens)
                and tokens[i + 1] == "("
            ):
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
                    while stack and stack[-1].type == TokenType.OPERATOR and self.OPERATORS[stack[-1].value] >= self.OPERATORS[token.value]:
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