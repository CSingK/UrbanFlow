def calculate_pob(queue_count: int, bus_occupancy: int, bus_capacity: int = 40) -> str:
    """
    Calculates the Probability of Boarding (PoB) using Net Capacity logic.
    Handles 'Ghost Queues' where queue_count is 0 by returning 'Data Pending'.
    """
    # Handle Ghost Queues
    if queue_count == 0:
        return "Data Pending"
        
    available_space = bus_capacity - bus_occupancy
    
    # Bus is full
    if available_space <= 0:
        return "Low"
        
    ratio = queue_count / available_space
    
    if ratio < 0.8:
        return "High"
    elif 0.8 <= ratio <= 1.1:
        return "Medium"
    else:
        return "Low"
