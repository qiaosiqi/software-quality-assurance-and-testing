package com.example.ae.tests;

import com.example.ae.model.UserData;
import com.example.ae.pages.HomePage;
import com.example.ae.pages.SignupLoginPage;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * 单个模块测试：
 * 1. 注册模块
 * 2. 登录模块
 * 3. 登出模块
 */
public class SingleModuleTest extends FlowHelper {

    @Test(description = "单模块：注册模块——填写信息创建新账户，验证 ACCOUNT CREATED!")
    public void registerModule_shouldCreateAccount() {
        UserData user = createFreshUser();
        HomePage homePage = registerAndStayLoggedIn(user);
        Assert.assertTrue(homePage.isLoggedInAs(user.getName()));
        deleteCurrentAccountIfPossible();
    }

    @Test(description = "单模块：登录模块——正确账号密码登录，验证登录成功")
    public void loginModule_shouldLoginWithCorrectPassword() {
        UserData user = createFreshUser();
        SignupLoginPage loginPage = registerThenLogout(user);

        HomePage homePage = loginPage.login(user.getEmail(), user.getPassword());
        Assert.assertTrue(homePage.isLoggedInAs(user.getName()), "正确账号密码登录后应显示 Logged in as 用户名");
        deleteCurrentAccountIfPossible();
    }

    @Test(description = "单模块：登录模块——错误账号密码登录，验证错误提示")
    public void loginModule_shouldShowErrorWithWrongPassword() {
        openHome();
        SignupLoginPage loginPage = new HomePage(driver, wait).clickSignupLogin();
        loginPage.loginExpectingStay("not_exist_" + System.nanoTime() + "@" + emailDomain, "WrongPassword");
        Assert.assertTrue(loginPage.hasLoginError(), "错误登录应显示 Your email or password is incorrect!");
    }

    @Test(description = "单模块：登出模块——登录后点击 Logout，验证跳回登录页")
    public void logoutModule_shouldReturnToLoginPage() {
        UserData user = createFreshUser();
        HomePage homePage = registerAndStayLoggedIn(user);

        SignupLoginPage loginPage = homePage.clickLogout();
        Assert.assertTrue(loginPage.isLoginPageDisplayed(), "登出后应返回 Signup/Login 页面");
    }
}
