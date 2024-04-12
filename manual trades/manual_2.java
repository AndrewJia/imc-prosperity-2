/**
 * we using java because my python be lacking xdd
 * basic 2D states / dp problem
 */

import java.util.*;

public class manual_2 {
    public static void main(String[] args) {
        double[][] dp = new double[4][7];    //4 currencies, 5 trades. cols 0 and 6 are start/end shells
        dp[3][0] = 100.0; //starting 100

        for(int c = 1; c <= 5; c++) {
            System.out.println("--------------- round "+ c + " ---------------");

            //shells
            System.out.print("best shells comes from ");
            dp[3][c] = multiMax(0.71*dp[0][c-1], 1.56*dp[1][c-1], 0.46*dp[2][c-1], 1.00*dp[3][c-1]);
            if (c==5) break;

            //pizza
            System.out.print("best pizza comes from ");
            dp[0][c] = multiMax(1.00*dp[0][c-1], 2.05*dp[1][c-1], 0.64*dp[2][c-1], 1.41*dp[3][c-1]);
            //wasabi
            System.out.print("best wasabi comes from ");
            dp[1][c] = multiMax(0.48*dp[0][c-1], 1.00*dp[1][c-1], 0.30*dp[2][c-1], 0.61*dp[3][c-1]);
            //snowball
            System.out.print("best snowball comes from ");
            dp[2][c] = multiMax(1.52*dp[0][c-1], 3.26*dp[1][c-1], 1.00*dp[2][c-1], 2.08*dp[3][c-1]);
            
        }
        
        for(int r = 0; r < 4; r++) {
            for(int c = 0; c < 6; c++) {
                System.out.print(String.format("%,06.2f", Double.valueOf(dp[r][c])) + " ");
            }
            System.out.println();
        }
    }

    // self explanatory
    public static double multiMax(double a, double b, double c, double d) {
        double result = Math.max(Math.max(a, b), Math.max(c, d));
        if(result == a) System.out.println("pizza");
        if(result == b) System.out.println("wasabi");
        if(result == c) System.out.println("snowball");
        if(result == d) System.out.println("shells");

        return result;
    }
}

