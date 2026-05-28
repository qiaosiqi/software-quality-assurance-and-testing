package com.example.ae.tests;

import com.example.ae.base.BaseTest;
import com.example.ae.model.UserData;
import com.example.ae.pages.*;

public class FlowHelper extends BaseTest {

    protected UserData createFreshUser() {
        return com.example.ae.utils.TestDataFactory.newUser(defaultUserName, defaultPassword, emailDomain);
    }

    protected HomePage registerAndStayLoggedIn(UserData user) {
        openHome();
        SignupLoginPage signupLoginPage = new HomePage(driver, wait).clickSignupLogin();
        AccountInformationPage accountInformationPage = signupLoginPage.submitSignup(user.getName(), user.getEmail());
        AccountCreatedPage accountCreatedPage = accountInformationPage.createAccount(user);
        org.testng.Assert.assertTrue(
                accountCreatedPage.getSuccessText().contains("ACCOUNT CREATED"),
                "注册成功页应显示 ACCOUNT CREATED!"
        );
        HomePage homePage = accountCreatedPage.clickContinue();
        if (!homePage.isLoggedInAs(user.getName())) {
            // 目标站有时注册成功后不会稳定保持登录态，改为使用刚注册的账号再登录一次，保证后续“登出/登录”模块可继续执行。
            openLogin();
            SignupLoginPage loginPage = new SignupLoginPage(driver, wait);
            homePage = loginPage.login(user.getEmail(), user.getPassword());
        }
        org.testng.Assert.assertTrue(homePage.hasLogoutLink() || homePage.isLoggedInAs(user.getName()), "注册/登录后应处于登录状态");
        return homePage;
    }

    protected SignupLoginPage registerThenLogout(UserData user) {
        HomePage homePage = registerAndStayLoggedIn(user);
        return homePage.clickLogout();
    }

    protected void deleteCurrentAccountIfPossible() {
        try {
            HomePage homePage = new HomePage(driver, wait);
            if (homePage.hasLogoutLink()) {
                AccountDeletedPage deletedPage = homePage.clickDeleteAccount();
                if (deletedPage.isDeletedDisplayed()) {
                    deletedPage.clickContinue();
                }
            }
        } catch (Exception ignored) {
            // 清理失败不影响主测试结论
        }
    }
}
