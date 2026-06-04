package com.example.ae.tests;

import com.example.ae.model.UserData;
import com.example.ae.pages.HomePage;
import com.example.ae.pages.SignupLoginPage;
import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.List;

/**
 * 数据组合测试：
 * 账号输入类型 5 种 × 密码输入类型 5 种 = 25 组。
 * validEmail/validPassword 均来自运行时动态注册账号，不写死。
 */
public class LoginDataCombinationTest extends FlowHelper {
    private static UserData sharedValidUser;
    private UserData validUser;

    @BeforeMethod(alwaysRun = true)
    public void prepareAccount() {
        // 25组数据组合测试只需要一个有效账号。避免每组都重新注册，减少超时和被网站限流的概率。
        if (sharedValidUser == null) {
            validUser = createFreshUser();
            registerThenLogout(validUser);
            sharedValidUser = validUser;
        } else {
            validUser = sharedValidUser;
        }
        openLogin();
    }

    @DataProvider(name = "loginCombinations")
    public Object[][] loginCombinations() {
        List<Object[]> rows = new ArrayList<>();

        String[][] emailCases = new String[][]{
                {"E1_VALID", "${validEmail}"},
                {"E2_NOT_EXIST", "not_exist_" + System.nanoTime() + "@" + emailDomain},
                {"E3_EMPTY", ""},
                {"E4_INVALID_FORMAT", "abc"},
                {"E5_UPPERCASE_VALID", "${validEmailUpper}"}
        };

        String[][] passwordCases = new String[][]{
                {"P1_VALID", "${validPassword}"},
                {"P2_WRONG", "${validPassword}_wrong"},
                {"P3_EMPTY", ""},
                {"P4_SHORT", "1"},
                {"P5_SPACE", " "}
        };

        for (String[] emailCase : emailCases) {
            for (String[] passwordCase : passwordCases) {
                String expected = expectedResult(emailCase[0], passwordCase[0]);
                rows.add(new Object[]{emailCase[0] + "+" + passwordCase[0], emailCase[1], passwordCase[1], expected});
            }
        }

        // 快速 demo 用 -Ddata.limit=N 只跑前 N 组；不设则返回全部 25 组（原行为）。
        String limitProp = System.getProperty("data.limit");
        if (limitProp != null && !limitProp.trim().isEmpty()) {
            try {
                int limit = Integer.parseInt(limitProp.trim());
                if (limit > 0 && limit < rows.size()) {
                    rows = new ArrayList<>(rows.subList(0, limit));
                }
            } catch (NumberFormatException ignored) {
                // 非法值忽略，跑全部
            }
        }

        return rows.toArray(new Object[0][]);
    }

    @Test(dataProvider = "loginCombinations", description = "数据组合：登录账号密码 25 组组合测试")
    public void loginCombination_shouldMatchExpectedResult(String caseId, String emailExpr, String passwordExpr, String expected) {
        SignupLoginPage loginPage = new SignupLoginPage(driver, wait);
        Assert.assertTrue(loginPage.isLoginPageDisplayed(), "前置条件：应位于登录页");

        String email = resolve(emailExpr);
        String password = resolve(passwordExpr);

        loginPage.loginExpectingStay(email, password);

        if ("SUCCESS".equals(expected)) {
            HomePage homePage = new HomePage(driver, wait).waitUntilLoaded();
            Assert.assertTrue(homePage.isLoggedInAs(validUser.getName()), caseId + " 应登录成功");
        } else if ("ERROR".equals(expected)) {
            Assert.assertTrue(loginPage.hasLoginError(), caseId + " 应显示账号或密码错误提示");
        } else if ("REQUIRED".equals(expected)) {
            boolean emailInvalid = hasHtml5ValidationMessage(loginPage.loginEmailInput());
            boolean passwordInvalid = hasHtml5ValidationMessage(loginPage.loginPasswordInput());
            Assert.assertTrue(emailInvalid || passwordInvalid, caseId + " 应触发 HTML5 必填/格式校验");
        } else {
            Assert.fail("未知 expected: " + expected);
        }
    }

    private String resolve(String expr) {
        return expr
                .replace("${validEmail}", validUser.getEmail())
                .replace("${validEmailUpper}", validUser.getEmail().toUpperCase())
                .replace("${validPassword}", validUser.getPassword());
    }

    private String expectedResult(String emailCase, String passwordCase) {
        if (emailCase.equals("E3_EMPTY") || emailCase.equals("E4_INVALID_FORMAT")
                || passwordCase.equals("P3_EMPTY")) {
            return "REQUIRED";
        }
        if (emailCase.equals("E1_VALID") && passwordCase.equals("P1_VALID")) {
            return "SUCCESS";
        }
        // 邮箱大小写是否等同由网站后端决定。为保证测试稳定，此处按错误登录处理。
        return "ERROR";
    }
}
