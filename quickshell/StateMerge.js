.pragma library
// JSON parsing creates fresh arrays/objects even when their contents did not change.
// Retain references so models and widget geometry do not reset on unrelated events.
function retainEqual(previous, incoming) {
    for (let key in incoming) {
        let value = incoming[key]
        if (value !== null && typeof value === "object" && previous[key] !== undefined
                && JSON.stringify(value) === JSON.stringify(previous[key]))
            incoming[key] = previous[key]
    }
    return incoming
}
