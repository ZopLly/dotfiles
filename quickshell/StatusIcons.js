.pragma library
function wifi(state) {
    if (!state.wifi_available) return "󰖪"
    if (!state.wifi) return "󰖪"
    if (!state.wifi_connected) return "󰖫"
    let signal = state.wifi_signal || 0
    return signal < 25 ? "󰤟" : signal < 50 ? "󰤢" : signal < 75 ? "󰤥" : "󰤨"
}
function volume(value, muted) {
    return muted ? "󰝟" : value < 0 ? "󰝟" : value === 0 ? "󰕿" : value < 50 ? "󰖀" : "󰕾"
}
function battery(info) {
    if (!info || info.percent < 0) return "󰂑"
    if (info.status === "Charging") return "󰂄"
    let icons = ["󰂎", "󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]
    return icons[Math.max(0, Math.min(10, Math.floor(info.percent/10)))]
}
function bluetooth(state) {
    return !state.bluetooth_available ? "󰂲" : !state.bluetooth ? "󰂲" : (state.bluetooth_devices || []).some(d => d.connected) ? "󰂱" : "󰂯"
}
