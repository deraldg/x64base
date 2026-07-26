# DD-047 CANDIDATE PATCH SKETCH — NOT APPLIED

This is not a drop-in patch. It is the intended shape of the repair.

Reason:
  cmd_replace.cpp currently contains the proven x64 memo text -> stored object-id
  conversion path. IMPORT should reuse a shared helper rather than copying
  private static functions into cmd_import.cpp.

Preferred extraction:
  include/cli/memo_field_store.hpp
  src/cli/memo_field_store.cpp

Candidate helper API:

```cpp
namespace dottalk::cli::memo_field_store {

bool is_x64_memo_field(const xbase::DbArea& A, int field1);

bool build_x64_memo_stored_value(xbase::DbArea& A,
                                 int field1,
                                 const std::string& user_value,
                                 std::string& stored_value_out,
                                 std::string& err_out);

} // namespace dottalk::cli::memo_field_store
```

Then cmd_replace.cpp should call the shared helper instead of its private static
build_x64_memo_stored_value.

cmd_import.cpp should change the inner import loop from:

```cpp
if (fi > 0) a.set(fi, cols[c]);
```

to the equivalent of:

```cpp
if (fi > 0) {
    std::string stored_value = cols[c];
    std::string memo_err;

    if (!dottalk::cli::memo_field_store::build_x64_memo_stored_value(
            a, fi, cols[c], stored_value, memo_err))
    {
        std::cout << "IMPORT: " << memo_err
                  << " at rec " << a.recno()
                  << ", column " << (c + 1) << ".\n";
        row_ok = false;
        break;
    }

    a.set(fi, stored_value);
}
```

Question to verify during implementation:
  For x64 M fields, does `a.set(fi, stored_object_id_string)` followed by
  `a.writeCurrent()` persist the object-id correctly after `appendBlank()`?

If not, IMPORT should use a stored-field write path compatible with the current
record, analogous to REPLACE's `replaceFieldStored(field1, stored_value, &err)`.
