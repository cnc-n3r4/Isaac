#pragma once

#include <memory>
#include <vector>
#include <mutex>
#include <type_traits>

namespace isaac {

/**
 * Simple memory pool for frequent allocations of the same type.
 * Reduces allocation overhead by reusing memory blocks.
 */
template<typename T>
class MemoryPool {
public:
    explicit MemoryPool(size_t initial_capacity = 100) {
        pool_.reserve(initial_capacity);
        for (size_t i = 0; i < initial_capacity; ++i) {
            pool_.push_back(std::make_unique<T>());
        }
    }

    template<typename... Args>
    T* allocate(Args&&... args) {
        std::lock_guard<std::mutex> lock(mutex_);

        // Try to find a free object
        for (auto& obj : pool_) {
            if (!obj->in_use_) {
                obj->in_use_ = true;
                // Reconstruct the object with new arguments
                obj->~T();
                new (obj.get()) T(std::forward<Args>(args)...);
                return obj.get();
            }
        }

        // No free objects, create new one
        auto new_obj = std::make_unique<T>(std::forward<Args>(args)...);
        new_obj->in_use_ = true;
        pool_.push_back(std::move(new_obj));
        return pool_.back().get();
    }

    void deallocate(T* obj) {
        std::lock_guard<std::mutex> lock(mutex_);

        // Find the object and mark as free
        for (auto& pool_obj : pool_) {
            if (pool_obj.get() == obj) {
                pool_obj->in_use_ = false;
                break;
            }
        }
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return pool_.size();
    }

    size_t available() const {
        std::lock_guard<std::mutex> lock(mutex_);
        size_t count = 0;
        for (const auto& obj : pool_) {
            if (!obj->in_use_) ++count;
        }
        return count;
    }

private:
    mutable std::mutex mutex_;
    std::vector<std::unique_ptr<T>> pool_;
};

/**
 * Base class for poolable objects.
 * Objects must inherit from this to work with MemoryPool.
 */
class Poolable {
public:
    Poolable() : in_use_(false) {}
    virtual ~Poolable() = default;

    bool in_use_;
};

/**
 * RAII wrapper for pooled objects.
 */
template<typename T>
class PooledObject {
public:
    PooledObject(MemoryPool<T>* pool, T* obj) : pool_(pool), obj_(obj) {}

    ~PooledObject() {
        if (pool_ && obj_) {
            pool_->deallocate(obj_);
        }
    }

    T* operator->() { return obj_; }
    T& operator*() { return *obj_; }
    T* get() { return obj_; }

    // Prevent copying
    PooledObject(const PooledObject&) = delete;
    PooledObject& operator=(const PooledObject&) = delete;

    // Allow moving
    PooledObject(PooledObject&& other) noexcept : pool_(other.pool_), obj_(other.obj_) {
        other.pool_ = nullptr;
        other.obj_ = nullptr;
    }

private:
    MemoryPool<T>* pool_;
    T* obj_;
};

} // namespace isaac