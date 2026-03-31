from dataclasses import dataclass
from typing import ClassVar, Dict, List
from symbolTranslator import *
from components import *
import re
import logging
logging.basicConfig(
    filename="log.txt",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s",
)

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

    def classify_tokens(self, expr: str) -> List[TokenT]:
        reg_pattern = self.TOKEN_PATTERN.split(expr)
        tokens =  [t.strip() for t in reg_pattern if t.strip()]
        classified = []
        for i, token in enumerate(tokens):
            if self.sym_set.is_operator(token):
                if token == ",":
                    classified.append(CommaToken())
                elif token == "(":
                    classified.append(OpeningRoundBracketToken())
                elif token == ")":
                    classified.append(ClosingRoundBracketToken())
                elif token == "{":
                    classified.append(OpeningSquigglyBracketToken())
                elif token == "}":
                    classified.append(ClosingSquigglyBracketToken())
                elif token not in "][]":
                    classified.append(OperatorToken(token))

            elif (i + 1 < len(tokens) and tokens[i + 1] == "("):
                classified.append(FunctionCallToken(token))   

            else:
                classified.append(TermToken(token))

        return classified   

    def to_postfix(self, tokens: List[TokenT]) -> List[TokenT]:
        output: List[TokenT] = []
        stack: List[TokenT] = []

        for token in tokens:
            match token:
                case TermToken():
                    output.append(token)
                case FunctionCallToken():
                    stack.append(token)
                case OperatorToken():
                    while (stack and isinstance(stack[-1], OperatorToken)
                           and self.sym_set.precedence(stack[-1].value) >= self.sym_set.precedence(token.value)):
                        output.append(stack.pop())
                    stack.append(token)
                case OpeningRoundBracketToken(): # We can use similar logic for curvy brackets for sets, but we will ignore for now
                    stack.append(token)
                case ClosingRoundBracketToken():
                    while stack and isinstance(stack[-1], OpeningRoundBracketToken) == False:
                        output.append(stack.pop())
                    if stack and isinstance(stack[-1], OpeningRoundBracketToken):
                        stack.pop()
                    if stack and isinstance(stack[-1], FunctionCallToken):
                        output.append(stack.pop())
                case OpeningSquigglyBracketToken():
                    output.append(OpeningSquigglyBracketToken()) # We will fill the set token later
                case ClosingSquigglyBracketToken():
                    set_elements: List[Union[TermToken, SetToken]] = []
                    while output and isinstance(output[-1], OpeningSquigglyBracketToken) == False:
                        set_elements.append(output.pop())
                    if output and isinstance(output[-1], OpeningSquigglyBracketToken):
                        output.pop()
                    output.append(SetToken(list(reversed(set_elements))))
                case CommaToken():
                    pass

        while stack:
            output.append(stack.pop())
        return output
    
    def translate(self, expr: str, context: TranslationContext = None) -> str:
        tokens = self.classify_tokens(expr)
        postfix_tokens = self.to_postfix(tokens)
        stack: List[TokenT] = []

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
            "÷": DivideTranslation(),
            "*": MultiplyTranslation(),
            "⇒": ImplicationTranslation(),
            "∧": AndTranslation(),
            "∨": OrTranslation(),
            "¬": NotTranslation(),
            "∈": MembershipTranslation(),
            "→": FunctionTypeTranslation(),
        }

        logging.debug(f"Translating expression: {expr}")
        for token in postfix_tokens:
            stack_values = [t.value for t in stack]
            logging.debug(f"     Processing token: {token}, Stack before processing: {stack_values}")
            if isinstance(token, TermToken):
                value = token.value if token.value not in ("TRUE", "FALSE") else token.value.lower()
                stack.append(TranslatedToken(value))

            elif isinstance(token, FunctionCallToken) or isinstance(token, OperatorToken):
                handler = handlers.get(token.value)
                if handler:
                    handler.translate(stack, context)
                else:
                    raise ValueError(f"No translation handler for operator/function: {token.value}")
            
            else:
                stack.append(token)
                
        if len(stack) != 1:
            raise ValueError("Invalid expression, stack should have exactly one element at the end of translation.")
        if not isinstance(stack[0], TranslatableToken):
            raise ValueError("Invalid expression, final token should be of type TRANSLATED.")
        
        translation = stack[0].get_translation()
        logging.debug(f"Final translated expression: {translation.replace(chr(10), ' [EOL] ')}")
        return "".join(translation).strip()