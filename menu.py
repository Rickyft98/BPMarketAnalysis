#!/usr/bin/env python3
"""
BLUE PROTOCOL - INTERACTIVE MENU
"""

from Calculator import ProfitCalculatorOptimized

def interactive_menu():
    """Interactive menu for the profit calculator"""
    calculator = ProfitCalculatorOptimized()
    
    while True:
        print("\n" + "="*60)
        print("💰 BLUE PROTOCOL - PROFIT CALCULATOR")
        print("="*60)
        print("1. 📊 Full Analysis (All Strategies)")
        print("2. 🔍 Analyze Specific Product")
        print("3. ⛏️ Only Gathering Analysis")
        print("4. 🛠️ Only Optimal Strategies")
        print("5. 📦 Show Available Products")
        print("6. ⚙️ Change Daily Focus (Current: 400)")
        print("7. 🚪 Exit")
        print("-" * 60)
        
        choice = input("Select an option (1-7): ").strip()
        
        if choice == '1':
            print("\n🔄 Running FULL analysis...")
            results = calculator.run_analysis()
            
            print("\n" + "="*60)
            print("FULL ANALYSIS RESULTS:")
            print("="*60)
            
            for key, df in results.items():
                if not df.empty:
                    print(f"\n{key.upper().replace('_', ' ')}:")
                    print("-" * 40)
                    
                    if key == 'optimal_strategies':
                        important_cols = ['Method', 'Crafted Units', 'Daily Profit', 'Luno/Focus', 
                                        'Focus Allocation', 'Total Materials Needed']
                        available_cols = [col for col in important_cols if col in df.columns]
                        print(df[available_cols].to_string(index=False))
                    
                    elif key == 'comprehensive':
                        print("TOP STRATEGIES:")
                        print(df.head(10).to_string(index=False))
                        print(f"\n📊 Total strategies: {len(df)}")
                    
                    else:
                        print(df.to_string(index=False))
            
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            # Get available products and display as numbered list
            available_products = calculator.get_available_products()
            
            if not available_products:
                print("\n❌ No products available for analysis.")
                input("\nPress Enter to continue...")
                continue
            
            print("\n📦 Available Products:")
            for i, product in enumerate(available_products, 1):
                print(f"   {i}. {product}")
            
            try:
                selection = int(input(f"\nSelect product (1-{len(available_products)}): "))
                
                if 1 <= selection <= len(available_products):
                    product_name = available_products[selection - 1]
                    result = calculator.analyze_single_product(product_name)
                    
                    if result:
                        print(f"\n✅ Analysis complete!")
                        print(f"   Product: {result['product']}")
                        print(f"   Daily Profit: {result['daily_profit']:,} Luno")
                        print(f"   Efficiency: {result['efficiency']:.1f} Luno/Focus")
                        print(f"   Strategy: {result['strategy']}")
                    else:
                        print(f"\n❌ Could not analyze '{product_name}'")
                else:
                    print(f"❌ Please enter a number between 1 and {len(available_products)}")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
            
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            print("\n⛏️ GATHERING ANALYSIS:")
            print("-" * 40)
            gathering_df = calculator.calculate_only_gathering()
            if not gathering_df.empty:
                print(gathering_df.to_string(index=False))
            else:
                print("No gathering data available")
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            print("\n🛠️ OPTIMAL STRATEGIES:")
            print("-" * 40)
            optimal_df = calculator.find_optimal_strategies()
            if not optimal_df.empty:
                important_cols = ['Method', 'Daily Profit', 'Luno/Focus', 'Focus Allocation']
                available_cols = [col for col in important_cols if col in optimal_df.columns]
                print(optimal_df[available_cols].to_string(index=False))
            else:
                print("No optimal strategies found")
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            calculator.show_available_products()
            input("\nPress Enter to continue...")
        
        elif choice == '6':
            try:
                new_focus = int(input("Enter new daily focus amount: "))
                if new_focus > 0:
                    calculator.daily_focus = new_focus
                    print(f"✅ Daily focus updated to: {new_focus}")
                else:
                    print("❌ Focus must be positive")
            except ValueError:
                print("❌ Please enter a valid number")
            input("\nPress Enter to continue...")
        
        elif choice == '7':
            print("\n👋 Thank you for using Blue Protocol Profit Calculator!")
            break
        
        else:
            print("❌ Invalid option. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    print("🚀 Starting Blue Protocol Profit Calculator...")
    interactive_menu()