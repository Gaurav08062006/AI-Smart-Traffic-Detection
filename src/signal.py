# src/signal.py

def get_signal(lane1, lane2, emergency):
    """
    Decide which lane gets green signal
    """

    # Emergency case
    if emergency:
        return "EMERGENCY", 60

    # Compare traffic density
    if lane1 > lane2:
        return "Lane 1 Green", 30
    elif lane2 > lane1:
        return "Lane 2 Green", 30
    else:
        return "Equal Traffic", 20