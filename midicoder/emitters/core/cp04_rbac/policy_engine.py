"""
CP04: RBAC & Policy Engine — ABAC Policy Engine.

Engine runtime cho Attribute-Based Access Control:
- Parse policy expression DSL thành AST
- Evaluate AST với PolicyContext
- Trả về PolicyDecision

Expression DSL syntax:
    "user.role == 'admin' AND resource.tenant_id == user.tenant_id"

Supported operators: ==, !=, in, not in, AND, OR, NOT, <, >, <=, >=
Supported variables: user.*, resource.*, action, env.*

Không cache (simplicity phase).
Tất cả comments bằng tiếng Việt.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Optional

from midicoder.emitters.core.cp04_rbac.models import (
    PolicyContext,
    PolicyDecision,
    PolicyRule,
    RBACConfig,
)


class PolicyEngine:
    """
    Policy Engine — Runtime engine cho ABAC Policy Evaluation.

    Engine parse policy expression DSL thành AST rồi evaluate với context.
    Không dùng eval() — sử dụng AST-based parser tự viết.
    """

    def __init__(self, config: RBACConfig) -> None:
        """
        Khởi tạo Policy Engine.

        Args:
            config: RBACConfig chứa policies
        """
        self._config = config

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """
        Evaluate tất cả policies với context, trả về final decision.

        Algorithm:
        1. Iterate qua tất cả policies
        2. Evaluate condition của mỗi policy
        3. Nếu DENY policy match → trả về DENY (deny takes precedence)
        4. Nếu ALLOW policy match → lưu lại
        5. Nếu có ít nhất một ALLOW match và không có DENY → ALLOW
        6. Nếu không có policy nào match → DENY mặc định

        Args:
            context: PolicyContext chứa user, resource, action, env

        Returns:
            PolicyDecision với kết quả final
        """
        deny_matched: Optional[PolicyRule] = None
        allow_matched: Optional[PolicyRule] = None

        for policy in self._config.policies:
            # Nếu policy có resource_type, kiểm tra resource match
            if policy.resource_type:
                resource_type = context.resource_attributes.get("type")
                if resource_type != policy.resource_type:
                    continue

            # Nếu policy có actions, kiểm tra action match
            if policy.actions and context.action not in policy.actions:
                continue

            # Evaluate condition
            try:
                result = self._evaluate_condition(policy.condition, context)
            except Exception as e:
                # Policy evaluation error → deny
                return PolicyDecision(
                    allowed=False,
                    policy_id=policy.id,
                    reason=f"Lỗi evaluate condition: {e}",
                )

            if result:
                if policy.effect == "deny":
                    deny_matched = policy
                else:
                    allow_matched = policy

        # DENY có precedence cao nhất
        if deny_matched is not None:
            return PolicyDecision(
                allowed=False,
                policy_id=deny_matched.id,
                reason=f"DENY policy '{deny_matched.id}' match",
            )

        # ALLOW nếu có ít nhất một allow policy match
        if allow_matched is not None:
            return PolicyDecision(
                allowed=True,
                policy_id=allow_matched.id,
                reason=f"ALLOW policy '{allow_matched.id}' match",
            )

        # Default deny
        return PolicyDecision(
            allowed=False,
            policy_id="",
            reason="Không có policy nào match — default DENY",
        )

    def evaluate_single(
        self, policy: PolicyRule, context: PolicyContext
    ) -> PolicyDecision:
        """
        Evaluate một policy riêng lẻ với context.

        Args:
            policy: PolicyRule để evaluate
            context: PolicyContext

        Returns:
            PolicyDecision
        """
        try:
            matched = self._evaluate_condition(policy.condition, context)
        except Exception as e:
            return PolicyDecision(
                allowed=False,
                policy_id=policy.id,
                reason=f"Lỗi evaluate condition: {e}",
            )

        if not matched:
            return PolicyDecision(
                allowed=False,
                policy_id=policy.id,
                reason="Condition không match",
            )

        return PolicyDecision(
            allowed=policy.effect == "allow",
            policy_id=policy.id,
            reason=f"Policy '{policy.id}' matched — effect: {policy.effect}",
        )

    def _evaluate_condition(
        self, condition: str, context: PolicyContext
    ) -> bool:
        """
        Evaluate condition expression với context.

        Parse expression thành tokens rồi evaluate AST.

        Args:
            condition: Expression string (ví dụ: "user.role == 'admin'")
            context: PolicyContext

        Returns:
            True nếu condition evaluate thành True
        """
        tokens = self._tokenize(condition)
        result, _ = self._parse_or_expr(tokens, context)
        return result

    # ========================================================================
    # Expression Parser — Recursive Descent AST Parser
    # ========================================================================

    def _tokenize(self, expr: str) -> list[tuple[str, Any]]:
        """
        Tokenize expression string thành danh sách tokens.

        Token types: ('IDENT', value), ('STRING', value), ('NUMBER', value),
                     ('BOOL', value), ('OP', value), ('AND', None), ('OR', None),
                     ('NOT', None), ('LPAREN', None), ('RPAREN', None)

        Args:
            expr: Expression string

        Returns:
            Danh sách (type, value) tokens
        """
        tokens: list[tuple[str, Any]] = []
        i = 0
        expr = expr.strip()

        while i < len(expr):
            ch = expr[i]

            # Skip whitespace
            if ch == " ":
                i += 1
                continue

            # String literal
            if ch in ("'", '"'):
                j = i + 1
                while j < len(expr) and expr[j] != ch:
                    j += 1
                value = expr[i + 1 : j]
                tokens.append(("STRING", value))
                i = j + 1
                continue

            # Number
            if ch.isdigit() or (ch == "-" and i + 1 < len(expr) and expr[i + 1].isdigit()):
                j = i + 1
                while j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
                    j += 1
                num_str = expr[i:j]
                value = float(num_str) if "." in num_str else int(num_str)
                tokens.append(("NUMBER", value))
                i = j
                continue

            # Multi-char operators & keywords
            remaining = expr[i:]
            for kw in ("not in", "<=", ">=", "!=", "==", "AND", "OR", "NOT", "in"):
                if remaining.startswith(kw):
                    if kw in ("AND", "OR", "NOT"):
                        tokens.append((kw, None))
                    elif kw == "not in":
                        tokens.append(("OP", "not in"))
                    else:
                        tokens.append(("OP", kw))
                    i += len(kw)
                    break
            else:
                # Single char
                if ch in ("<", ">"):
                    tokens.append(("OP", ch))
                    i += 1
                elif ch == "(":
                    tokens.append(("LPAREN", None))
                    i += 1
                elif ch == ")":
                    tokens.append(("RPAREN", None))
                    i += 1
                elif ch.isalpha() or ch == "_":
                    j = i
                    while j < len(expr) and (expr[j].isalnum() or expr[j] in ("_", ".")):
                        j += 1
                    tokens.append(("IDENT", expr[i:j]))
                    i = j
                else:
                    # Unknown char — skip
                    i += 1

        return tokens

    def _resolve_variable(self, name: str, context: PolicyContext) -> Any:
        """
        Resolve variable name thành giá trị từ context.

        Mapping:
        - user.* → context.user_attributes
        - resource.* → context.resource_attributes
        - action → context.action
        - env.* → context.environment
        - true/true → True, false → False

        Args:
            name: Variable name (ví dụ: "user.role")
            context: PolicyContext

        Returns:
            Giá trị của variable
        """
        # Boolean literals
        if name.lower() == "true":
            return True
        if name.lower() == "false":
            return False
        if name.lower() == "none":
            return None

        # action
        if name == "action":
            return context.action

        # user.*
        if name.startswith("user."):
            attr = name[5:]  # sau "user."
            return context.user_attributes.get(attr)

        # resource.*
        if name.startswith("resource."):
            attr = name[9:]  # sau "resource."
            return context.resource_attributes.get(attr)

        # env.*
        if name.startswith("env."):
            attr = name[4:]  # sau "env."
            return context.environment.get(attr)

        # Plain identifier — try context.get()
        return context.get(name)

    def _parse_or_expr(
        self, tokens: list[tuple[str, Any]], context: PolicyContext
    ) -> tuple[bool, list]:
        """
        Parse OR expression (thấp nhất precedence).

        or_expr := and_expr (OR and_expr)*

        Returns:
            (result, remaining_tokens)
        """
        left, tokens = self._parse_and_expr(tokens, context)

        while tokens and tokens[0] == ("OR", None):
            tokens = tokens[1:]  # consume OR
            right, tokens = self._parse_and_expr(tokens, context)
            left = left or right

        return left, tokens

    def _parse_and_expr(
        self, tokens: list[tuple[str, Any]], context: PolicyContext
    ) -> tuple[bool, list]:
        """
        Parse AND expression.

        and_expr := not_expr (AND not_expr)*

        Returns:
            (result, remaining_tokens)
        """
        left, tokens = self._parse_not_expr(tokens, context)

        while tokens and tokens[0] == ("AND", None):
            tokens = tokens[1:]  # consume AND
            right, tokens = self._parse_not_expr(tokens, context)
            left = left and right

        return left, tokens

    def _parse_not_expr(
        self, tokens: list[tuple[str, Any]], context: PolicyContext
    ) -> tuple[bool, list]:
        """
        Parse NOT expression.

        not_expr := NOT not_expr | comparison

        Returns:
            (result, remaining_tokens)
        """
        if tokens and tokens[0] == ("NOT", None):
            tokens = tokens[1:]  # consume NOT
            result, tokens = self._parse_not_expr(tokens, context)
            return not result, tokens

        return self._parse_comparison(tokens, context)

    def _parse_comparison(
        self, tokens: list[tuple[str, Any]], context: PolicyContext
    ) -> tuple[bool, list]:
        """
        Parse comparison expression.

        comparison := primary OP primary | primary (in | not in) primary

        Returns:
            (result, remaining_tokens)
        """
        left_val, tokens = self._parse_primary(tokens, context)

        if tokens and tokens[0][0] == "OP":
            op = tokens[0][1]
            tokens = tokens[1:]
            right_val, tokens = self._parse_primary(tokens, context)

            return self._apply_operator(op, left_val, right_val), tokens

        # Single value — truthy
        return bool(left_val), tokens

    def _parse_primary(
        self, tokens: list[tuple[str, Any]], context: PolicyContext
    ) -> tuple[Any, list]:
        """
        Parse primary expression (literal, variable, parenthesized expr).

        Returns:
            (value, remaining_tokens)
        """
        if not tokens:
            return None, tokens

        token = tokens[0]

        # Parenthesized expression
        if token == ("LPAREN", None):
            tokens = tokens[1:]  # consume (
            result, tokens = self._parse_or_expr(tokens, context)
            if tokens and tokens[0] == ("RPAREN", None):
                tokens = tokens[1:]  # consume )
            return result, tokens

        # String literal
        if token[0] == "STRING":
            return token[1], tokens[1:]

        # Number literal
        if token[0] == "NUMBER":
            return token[1], tokens[1:]

        # Identifier — resolve variable
        if token[0] == "IDENT":
            value = self._resolve_variable(token[1], context)
            return value, tokens[1:]

        # Unknown token
        return None, tokens[1:]

    def _apply_operator(self, op: str, left: Any, right: Any) -> bool:
        """
        Apply operator giữa left và right.

        Args:
            op: Operator string
            left: Left operand value
            right: Right operand value

        Returns:
            Kết quả boolean
        """
        try:
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left is not None and left < right
            if op == ">":
                return left is not None and left > right
            if op == "<=":
                return left is not None and left <= right
            if op == ">=":
                return left is not None and left >= right
            if op == "in":
                return right is not None and left in right
            if op == "not in":
                return right is not None and left not in right
        except TypeError:
            return False
        return False