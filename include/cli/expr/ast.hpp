// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace dottalk { namespace expr {

struct RecordView {
    std::function<std::string(std::string_view)> get_field_str;
    std::function<std::optional<double>(std::string_view)> get_field_num;
    std::function<std::optional<char>(std::string_view)> get_field_type;

    // ISNULL()'s accessor, and it is deliberately NOT a value accessor.
    //
    // A null field's value is the empty string. So is a blank field's. Every
    // accessor above therefore returns the SAME thing for both, which is why
    // ISNULL cannot be an ordinary function over an evaluated argument: it
    // would be handed "" and asked to distinguish null from blank, the one
    // question it exists to answer.
    //
    // nullopt means "no such field" and becomes an error at the call site,
    // matching how an unknown field behaves everywhere else. A field that
    // EXISTS but cannot be null answers false -- that is the true answer, not
    // an error. A row source that has no null concept at all leaves this unset,
    // and ISNULL() then refuses rather than answering "not null", because a
    // confident false here is a wrong answer that looks like a right one.
    std::function<std::optional<bool>(std::string_view)> get_field_is_null;
};

struct Expr {
    virtual ~Expr() = default;
    virtual bool eval(const RecordView& rv) const = 0;

    // Allow expressions to return string results (DATEADD, DTOC, etc.)
    virtual std::string evalString(const RecordView& rv) const {
        // Default: convert bool result to ".T." / ".F." (FoxPro-ish)
        return eval(rv) ? ".T." : ".F.";
    }
};

struct LitString : Expr {
    std::string v;
    explicit LitString(std::string s) : v(std::move(s)) {}
    bool eval(const RecordView&) const override { return !v.empty(); }
    std::string evalString(const RecordView&) const override { return v; }
};

struct LitNumber : Expr {
    double v;
    explicit LitNumber(double d) : v(d) {}
    bool eval(const RecordView&) const override { return v != 0.0; }
    std::string evalString(const RecordView&) const override {
        return std::to_string(v);
    }
};

struct LitBool : Expr {
    bool v;
    explicit LitBool(bool value) : v(value) {}
    bool eval(const RecordView&) const override { return v; }
    std::string evalString(const RecordView&) const override { return v ? ".T." : ".F."; }
};

struct FieldRef : Expr {
    std::string name;
    explicit FieldRef(std::string n) : name(std::move(n)) {}
    bool eval(const RecordView& rv) const override;
    std::string evalString(const RecordView& rv) const override;
};

struct FunctionCall : Expr {
    std::string name;
    std::vector<std::unique_ptr<Expr>> args;
    FunctionCall(std::string n, std::vector<std::unique_ptr<Expr>> a)
        : name(std::move(n)), args(std::move(a)) {}
    bool eval(const RecordView& rv) const override;
    std::string evalString(const RecordView& rv) const override;
};

enum class CmpOp { EQ, NE, LT, LE, GT, GE };

struct Cmp : Expr {
    std::unique_ptr<Expr> lhs, rhs;
    CmpOp op;
    Cmp(std::unique_ptr<Expr> L, CmpOp O, std::unique_ptr<Expr> R)
        : lhs(std::move(L)), rhs(std::move(R)), op(O) {}
    bool eval(const RecordView& rv) const override;
};

enum class BoolOp { AND, OR };

struct BoolBin : Expr {
    std::unique_ptr<Expr> lhs, rhs;
    BoolOp op;
    BoolBin(std::unique_ptr<Expr> L, BoolOp O, std::unique_ptr<Expr> R)
        : lhs(std::move(L)), rhs(std::move(R)), op(O) {}
    bool eval(const RecordView& rv) const override;
};

struct Not : Expr {
    std::unique_ptr<Expr> inner;
    explicit Not(std::unique_ptr<Expr> e) : inner(std::move(e)) {}
    bool eval(const RecordView& rv) const override;
};

// ---------- Arithmetic ----------
enum class ArithOp { Add, Sub, Mul, Div };

struct Arith : Expr {
    std::unique_ptr<Expr> lhs, rhs;
    ArithOp op;
    Arith(std::unique_ptr<Expr> L, ArithOp O, std::unique_ptr<Expr> R)
        : lhs(std::move(L)), rhs(std::move(R)), op(O) {}
    bool   eval(const RecordView& rv) const override;
    double evalNumber(const RecordView& rv) const;

    std::string evalString(const RecordView& rv) const override {
        return std::to_string(evalNumber(rv));
    }
};

}} // namespace dottalk::expr
