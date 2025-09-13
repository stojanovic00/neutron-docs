#!/usr/bin/env python3
"""
Neutron DEX Tick-Price Converter

Based on the Neutron DEX implementation:
- Formula: price = 1.0001^tick for positive ticks
- Formula: price = 1 / (1.0001^|tick|) for negative ticks
- Comment from code: "tickIndex refers to the index of a specified tick such that x * 1.0001 ^(1 * t) = y"
"""

import math
from decimal import Decimal, getcontext

# Set high precision for accurate calculations
getcontext().prec = 50

class NeutronDexConverter:
    BASE = Decimal("1.0001")
    MAX_TICK = 559680  # From types/price.go MaxTickExp
    MIN_PRICE = Decimal("0.000000000000000000000000495")
    MAX_PRICE = Decimal("2020125331305056766452345.127500016657360222036663651")
    
    @classmethod
    def tick_to_price(cls, tick: int) -> Decimal:
        """
        Convert tick index to price (0to1 price: Token0 -> Token1)
        
        Args:
            tick: Tick index (can be positive or negative)
            
        Returns:
            Price as Decimal
            
        Raises:
            ValueError: If tick is out of valid range
        """
        if abs(tick) > cls.MAX_TICK:
            raise ValueError(f"Tick {tick} is out of range. Max: ±{cls.MAX_TICK}")
        
        if tick >= 0:
            # For positive ticks: price = 1.0001^tick
            price = cls.BASE ** tick
        else:
            # For negative ticks: price = 1 / (1.0001^|tick|)
            price = Decimal("1") / (cls.BASE ** abs(tick))
        
        return price
    
    @classmethod
    def price_to_tick(cls, price: Decimal) -> int:
        """
        Convert price to tick index
        
        Args:
            price: Price value (must be positive)
            
        Returns:
            Tick index as integer
            
        Raises:
            ValueError: If price is out of valid range
        """
        if price <= 0:
            raise ValueError("Price must be positive")
        
        if price < cls.MIN_PRICE or price > cls.MAX_PRICE:
            raise ValueError(f"Price {price} is out of valid range [{cls.MIN_PRICE}, {cls.MAX_PRICE}]")
        
        if price >= 1:
            # For prices >= 1: tick = log(price) / log(1.0001)
            tick = math.log(float(price)) / math.log(float(cls.BASE))
        else:
            # For prices < 1: tick = -log(1/price) / log(1.0001)
            tick = -math.log(float(1/price)) / math.log(float(cls.BASE))
        
        return round(tick)
    
    @classmethod
    def price_0to1_to_1to0(cls, price_0to1: Decimal) -> Decimal:
        """Convert 0to1 price to 1to0 price (inverse)"""
        return Decimal("1") / price_0to1
    
    @classmethod
    def validate_conversion(cls, tick: int, tolerance: Decimal = Decimal("0.01")) -> bool:
        """
        Validate that tick -> price -> tick conversion is accurate
        
        Args:
            tick: Original tick index
            tolerance: Acceptable percentage error (default 1%)
            
        Returns:
            True if conversion is accurate within tolerance
        """
        try:
            price = cls.tick_to_price(tick)
            tick_back = cls.price_to_tick(price)
            error = abs(tick - tick_back)
            return error <= 1  # Allow ±1 tick error due to rounding
        except ValueError:
            return False


def main():
    """Interactive tick-price converter"""
    converter = NeutronDexConverter()
    
    print("🔄 Neutron DEX Interactive Tick-Price Converter")
    print("=" * 60)
    print("Commands:")
    print("  t <tick>   - Convert tick to price")
    print("  p <price>  - Convert price to tick") 
    print("  q or quit  - Exit")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n> ").strip().lower()
            
            if user_input in ['q', 'quit', 'exit']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
                
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ Invalid format. Use: 't <tick>' or 'p <price>'")
                continue
                
            command, value = parts[0], parts[1]
            
            if command == 't':
                # Tick to price conversion
                try:
                    tick = int(value)
                    price_0to1 = converter.tick_to_price(tick)
                    price_1to0 = converter.price_0to1_to_1to0(price_0to1)
                    
                    print(f"📊 Tick {tick}:")
                    print(f"   0to1 Price: {price_0to1:.10f}")
                    print(f"   1to0 Price: {price_1to0:.10f}")
                    
                except ValueError as e:
                    if "invalid literal" in str(e):
                        print(f"❌ Invalid tick: '{value}' is not a valid integer")
                    else:
                        print(f"❌ Error: {e}")
                        
            elif command == 'p':
                # Price to tick conversion
                try:
                    price = Decimal(value)
                    tick = converter.price_to_tick(price)
                    price_back = converter.tick_to_price(tick)
                    price_inverse = converter.price_0to1_to_1to0(price)
                    
                    print(f"💰 Price {price}:")
                    print(f"   Tick: {tick}")
                    print(f"   Verified Price: {price_back:.10f}")
                    print(f"   Inverse Price: {price_inverse:.10f}")
                    
                except ValueError as e:
                    if "Invalid decimal" in str(e) or "invalid literal" in str(e):
                        print(f"❌ Invalid price: '{value}' is not a valid number")
                    else:
                        print(f"❌ Error: {e}")
                        
            else:
                print(f"❌ Unknown command: '{command}'. Use 't' or 'p'")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
