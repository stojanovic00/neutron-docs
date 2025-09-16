package keeper_test

import (
	"cosmossdk.io/math"
	sdkmath "cosmossdk.io/math"
	"github.com/neutron-org/neutron/v8/x/dex/types"
)

// In all tests TokenA and TokenB are used which should be ATOM and USDC in that order
// ATOM being token0 and USDC being token1
func (s *DexTestSuite) TestDepositSymetrical() {
	s.fundAliceBalances(50, 50)

	// GIVEN
	// create spread around -5, 5
	// s.aliceDeposits(NewDeposit(10, 10, 0, 5))
	s.aliceDeposits(NewDeposit(10, 10, 0, 5))
	s.assertAliceBalances(40, 40)
	s.assertDexBalances(10, 10)
	s.assertCurr1To0(-5)
	s.assertCurr0To1(5)

	// WHEN
	// deposit in spread (10 of A at tick 0 fee 1)
	s.aliceDeposits(NewDeposit(10, 0, 0, 1))
	s.assertAliceBalances(30, 40)
	s.assertDexBalances(20, 10)

	// THEN
	// assert currentTick1To0 moved
	s.assertCurr1To0(-1)
}

func (s *DexTestSuite) TestPoolCreationExample() {
	s.fundAliceBalances(50, 50)

	s.aliceDeposits(NewDeposit(10, 10, 3, 1))
	s.assertAliceBalances(40, 40)
	s.assertDexBalances(10, 10)
	s.assertCurr0To1(4)
	// This fails, it normalizes to +2
	s.assertCurr1To0(-2)
}

// Notice that even though ticks is 23027 meaning price is 10 USDC per ATOM
// Ratio in this pool should be 1:10 but we are allowed to deposit same amount of TookenA and TokenB
// This is allowed only on freshly created pools
func (s *DexTestSuite) TestSuiteProblems() {
	s.fundAliceBalances(100, 100)

	// GIVEN: 1 ATOM = 10 USDC (tick ~23027)
	// Create liquidity around this price with fee=1
	// Center tick will be at 23027, creating pool at ticks (23027-1=23026) and (23027+1=23028)
	s.aliceDeposits(NewDeposit(10, 10, 23027, 0))

	s.assertAliceBalances(90, 90)
	s.assertDexBalances(10, 10)

	// Pool should be created with:
	// - UpperTick1 (USDC side): tick 23027
	// - LowerTick0 (ATOM side): tick -23027
	s.assertCurr0To1(23027) // Current tick for ATOM→USDC direction
	//This function normalizes one more thus making it positive
	s.assertCurr1To0(23027) // Current tick for USDC→ATOM direction (should be negative!)
	// Even though lower tick on -23027 this function reads pool by id and takes its
	//  resservers, only when we provide 23027 (not -23027)  and will show both negative and positive tick liquidities here
	s.assertLiquidityAtTick(10, 10, 23027, 0)
}

func (s *DexTestSuite) TestBelExample() {
	s.fundAliceBalances(50, 50)

	// GIVEN TokenA liquidity at tick 2002-2005
	s.aliceDeposits(NewDeposit(10, 0, -2001, 1),
		NewDeposit(10, 0, -2003, 1),
		NewDeposit(10, 0, -2004, 1),
	)
	// WHEN alice deposits TokenB at tick -2003 (BEL)
	// THEN FAILURE
	s.assertAliceDepositFails(
		types.ErrDepositBehindEnemyLines,
		NewDepositWithOptions(0, 50, -2004, 1, types.DepositOptions{FailTxOnBel: true}),
	)
}

func (s *DexTestSuite) TestSwapOnDepositExample() {
	s.fundAliceBalances(50, 0)
	s.fundBobBalances(0, 30)

	// GIVEN TokenB liquidity at tick 2002-2004
	s.bobDeposits(NewDeposit(0, 10, 2001, 1),
		NewDeposit(0, 10, 2002, 1),
		NewDeposit(0, 10, 2003, 1),
	)
	// WHEN alice deposits TokenA at tick -2005 (BEL)
	resp := s.aliceDeposits(
		NewDepositWithOptions(50, 0, 2006, 1, types.DepositOptions{FailTxOnBel: true, SwapOnDeposit: true}),
	)

	// THEN some of alice's tokenA is swapped and she deposits ~13TokenA & ~30TokenB
	// A = 50 - 30 * 1.0001^~2003 = 13.3
	// SharesIssued = 13.3 + 30 * 1.0001^2006 = ~50

	s.Equal(sdkmath.NewInt(13347290), resp.Reserve0Deposited[0])
	s.Equal(sdkmath.NewInt(30000000), resp.Reserve1Deposited[0])
	s.Equal(sdkmath.NewInt(50010996), resp.SharesIssued[0].Amount)
	s.assertAliceBalances(0, 0)

	s.assertLiquidityAtTickInt(sdkmath.NewInt(13347289), sdkmath.NewInt(30000000), 2006, 1)
}
func (s *DexTestSuite) TestAutoswapExample() {
	s.fundAliceBalances(50, 50)
	s.fundBobBalances(50, 0)

	// GIVEN a pool with double-sided liquidity
	s.aliceDeposits(NewDeposit(50, 50, 2000, 2))
	s.assertAccountSharesInt(s.alice, 2000, 2, math.NewInt(111069527))

	// WHEN bob deposits only TokenA
	s.bobDeposits(NewDeposit(50, 0, 2000, 2))
	s.assertPoolLiquidity(100, 50, 2000, 2)

	// THEN his deposit is autoswapped
	// He receives 49.985501 shares
	// swapAmount = 27.491577 Token0 see pool.go for the math
	// (50 - 27.491577) / ( 27.491577 / 1.0001^2000) = 1 ie. pool ratio is maintained
	// depositValue = depositAmount - (autoswapedAmountAsToken0 * fee)
	//              = 50 - 27.491577 * (1 - 1.0001^-2)
	//              = 49.9945025092
	// SharesIssued = depositValue * existing shares / (existingValue + autoSwapFee)
	//              = 49.9945025092 * 111.069527 / (111.069527 + .005497490762642563860802206452577)
	//              = 49.992027

	s.assertAccountSharesInt(s.bob, 2000, 2, math.NewInt(49992027))
}
