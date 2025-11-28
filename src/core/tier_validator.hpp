#pragma once

#include <map>
#include <string>
#include <vector>

namespace isaac {

class TierValidator {
public:
    TierValidator();
    ~TierValidator();

    // Get safety tier for a command (1-4)
    // 1 = instant execution, 2 = safe, 2.5 = confirm, 3 = validate, 4 = lockdown
    float get_tier(const std::string& command) const;

    // Convenience methods
    bool is_safe(const std::string& command) const;
    bool requires_confirmation(const std::string& command) const;
    bool requires_validation(const std::string& command) const;

private:
    void load_tier_defaults();
    bool load_from_file();
    void load_hardcoded_defaults();
    void parse_json(const std::string& json_content);

    std::map<std::string, std::vector<std::string>> tier_defaults_;
};

} // namespace isaac