#!/usr/bin/env python3
"""
Neutron DEX Tick-Price Calculator

Interactive tool for converting between tick indexes and prices
Based on the Neutron DEX implementation using the formula: price = 1.0001^tick
"""

import math
from decimal import Decimal, getcontext
import sys

# Set high precision for accurate calculations
getcontext().prec = 50

class NeutronDexCalculator:
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
        """
        if abs(tick) > cls.MAX_TICK:
            raise ValueError(f"Tick {tick} is out of range [±{cls.MAX_TICK}]")
        
        if tick < 0:
            # For negative ticks: price = 1 / (1.0001^|tick|)
            return Decimal("1") / (cls.BASE ** abs(tick))
        else:
            # For positive ticks: price = 1.0001^tick
            return cls.BASE ** tick
    
    @classmethod
    def price_to_tick(cls, price: Decimal) -> int:
        """
        Convert price to tick index
        
        Args:
            price: Price as Decimal
            
        Returns:
            Tick index as integer
        """
        if price <= 0:
            raise ValueError("Price must be positive")
        
        if price < cls.MIN_PRICE or price > cls.MAX_PRICE:
            raise ValueError(f"Price {price} is out of range [{cls.MIN_PRICE}, {cls.MAX_PRICE}]")
        
        if price < 1:
            # For prices < 1, calculate positive tick then negate
            inverse_price = Decimal("1") / price
            tick = int(round(float(inverse_price.ln() / cls.BASE.ln())))
            return -tick
        else:
            # For prices >= 1, calculate directly
            tick = int(round(float(price.ln() / cls.BASE.ln())))
            return tick
    
    @classmethod
    def price_0to1_to_1to0(cls, price_0to1: Decimal) -> Decimal:
        """Convert 0to1 price to 1to0 price (simple inverse)"""
        return Decimal("1") / price_0to1
    
    @classmethod
    def validate_round_trip(cls, tick: int) -> bool:
        """Test if tick -> price -> tick conversion is accurate"""
        try:
            price = cls.tick_to_price(tick)
            tick_back = cls.price_to_tick(price)
            return abs(tick - tick_back) <= 1  # Allow 1 tick difference due to rounding
        except:
            return False

def print_header():
    """Print the application header"""
    print("🔄 Neutron DEX Interactive Tick-Price Calculator")
    print("=" * 60)
    print("Commands:")
    print("  t <tick>   - Convert tick to price")
    print("  p <price>  - Convert price to tick")
    print("  h or help  - Show this help")
    print("  q or quit  - Exit")
    print("=" * 60)

def format_price(price: Decimal) -> str:
    """Format price for display"""
    if price == 0:
        return "0"
    elif price < Decimal("0.000001"):
        return f"{price:.2e}"
    elif price < 1:
        return f"{price:.10f}".rstrip('0').rstrip('.')
    elif price < 1000:
        return f"{price:.10f}".rstrip('0').rstrip('.')
    else:
        return f"{price:.6f}".rstrip('0').rstrip('.')

def handle_tick_command(tick_str: str):
    """Handle tick to price conversion"""
    try:
        tick = int(tick_str)
        price_0to1 = NeutronDexCalculator.tick_to_price(tick)
        price_1to0 = NeutronDexCalculator.price_0to1_to_1to0(price_0to1)
        
        print(f"📊 Tick {tick}:")
        print(f"   0to1 Price: {format_price(price_0to1)}")
        print(f"   1to0 Price: {format_price(price_1to0)}")
        
        # Verify round-trip accuracy
        if NeutronDexCalculator.validate_round_trip(tick):
            print(f"   ✅ Round-trip accurate")
        else:
            print(f"   ⚠️  Round-trip has small error (normal for extreme values)")
            
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def handle_price_command(price_str: str):
    """Handle price to tick conversion"""
    try:
        price = Decimal(price_str)
        tick = NeutronDexCalculator.price_to_tick(price)
        verified_price = NeutronDexCalculator.tick_to_price(tick)
        inverse_price = NeutronDexCalculator.price_0to1_to_1to0(price)
        
        print(f"💰 Price {format_price(price)}:")
        print(f"   Tick: {tick}")
        print(f"   Verified Price: {format_price(verified_price)}")
        print(f"   Inverse Price: {format_price(inverse_price)}")
        
        # Show accuracy
        accuracy = abs(price - verified_price) / price * 100
        if accuracy < 0.001:
            print(f"   ✅ High accuracy ({accuracy:.6f}% difference)")
        else:
            print(f"   ⚠️  Accuracy: {accuracy:.6f}% difference")
            
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_examples():
    """Show some example calculations"""
    print("\n💡 Examples:")
    print("-" * 40)
    examples = [
        (0, "1:1 price ratio"),
        (23027, "~10:1 price ratio"), 
        (-23027, "~0.1:1 price ratio"),
        (69078, "~1000:1 price ratio"),
        (-69078, "~0.001:1 price ratio")
    ]
    
    for tick, description in examples:
        price = NeutronDexCalculator.tick_to_price(tick)
        print(f"  Tick {tick:6d} = {format_price(price):>15s} ({description})")
    print()

def main():
    """Main interactive loop"""
    print_header()
    show_examples()
    
    while True:
        try:
            user_input = input("> ").strip().lower()
            
            if not user_input:
                continue
                
            if user_input in ['q', 'quit', 'exit']:
                print("👋 Goodbye!")
                break
                
            if user_input in ['h', 'help']:
                print_header()
                show_examples()
                continue
                
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ Invalid format. Use: t <tick> or p <price>")
                continue
                
            command, value = parts
            
            if command == 't':
                handle_tick_command(value)
            elif command == 'p':
                handle_price_command(value)
            else:
                print("❌ Unknown command. Use 't' for tick or 'p' for price")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
