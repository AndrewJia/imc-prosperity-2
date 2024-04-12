/**
 * we using java because my python be lacking xdd
 * basic 2D states / dp problem
 */

import java.util.*;

public class manual_2 {
    public static void main(String[] args) {
        double[][] dp = new double[4][6];    //4 currencies, 5 trades
        dp[3][0] = 100.0; //starting 100

        for(int c = 1; c <= 5; c++) {
            //pizza
            dp[0][c] = multiMax(1.00*dp[0][c-1], 2.05*dp[1][c-1], 0.64*dp[2][c-1], 1.41*dp[3][c-1]);
            //wasabi
            dp[1][c] = multiMax(0.48*dp[0][c-1], 1.00*dp[1][c-1], 0.30*dp[2][c-1], 0.61*dp[3][c-1]);
            //snowball
            dp[2][c] = multiMax(1.52*dp[0][c-1], 3.26*dp[1][c-1], 1.00*dp[2][c-1], 2.08*dp[3][c-1]);
            //shells
            dp[3][c] = multiMax(0.71*dp[0][c-1], 1.56*dp[1][c-1], 0.46*dp[2][c-1], 1.00*dp[3][c-1]);
        }
        System.out.println(dp[3][5]); //print max ending shells
        for(int r = 0; r < 4; r++) {
            for(int c = 0; c < 5; c++) {
                System.out.print(String.format("%,06.2f", Double.valueOf(dp[r][c])) + " ");
            }
            System.out.println();
        }
    }

    // self explanatory
    public static double multiMax(double a, double b, double c, double d) {
        return Math.max(Math.max(a, b), Math.max(c, d));
    }
}

