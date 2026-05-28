package com.example.ae.tests;

import com.example.ae.model.UserData;
import com.example.ae.pages.HomePage;
import com.example.ae.pages.SignupLoginPage;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * 集成模块测试。
 *
 * 深度说明：
 * 深度 = 业务模块节点数。
 * 因为本题只限定注册、登录、登出三个模块，所以深度≥4时需要重复使用登录/登出动作；
 * 这里的“不重复”理解为不重复题目截图中已有的路径。
 */
public class IntegrationModuleTest extends FlowHelper {

    @Test(description = "集成路径A，深度4：注册 -> 登出 -> 正确登录 -> 登出")
    public void integration_depth4_registerLogoutLoginLogout() {
        UserData user = createFreshUser();

        // 1 注册
        HomePage homePage = registerAndStayLoggedIn(user);
        Assert.assertTrue(homePage.isLoggedInAs(user.getName()));

        // 2 登出
        SignupLoginPage loginPage = homePage.clickLogout();
        Assert.assertTrue(loginPage.isLoginPageDisplayed());

        // 3 正确登录
        HomePage afterLogin = loginPage.login(user.getEmail(), user.getPassword());
        Assert.assertTrue(afterLogin.isLoggedInAs(user.getName()));

        // 4 再次登出
        SignupLoginPage afterLogout = afterLogin.clickLogout();
        Assert.assertTrue(afterLogout.isLoginPageDisplayed());
    }

    @Test(description = "自定义不重复集成路径B，深度5：注册 -> 登出 -> 错误登录 -> 正确登录 -> 登出")
    public void integration_depth5_registerLogoutWrongLoginCorrectLoginLogout() {
        UserData user = createFreshUser();

        // 1 注册模块：创建新账号，并验证 ACCOUNT CREATED!
        HomePage homePage = registerAndStayLoggedIn(user);

        // 2 登出模块：清除当前会话，回到登录页
        SignupLoginPage loginPage = homePage.clickLogout();
        Assert.assertTrue(loginPage.isLoginPageDisplayed(), "登出后应回到登录页");

        // 3 登录模块-错误分支：使用同一账号但错误密码，验证错误提示
        loginPage.loginExpectingStay(user.getEmail(), user.getPassword() + "_wrong");
        Assert.assertTrue(loginPage.hasLoginError(), "错误密码应显示错误提示");

        // 4 登录模块-正确分支：使用正确账号密码重新登录，验证会话恢复
        HomePage afterCorrectLogin = loginPage.login(user.getEmail(), user.getPassword());
        Assert.assertTrue(afterCorrectLogin.isLoggedInAs(user.getName()), "正确登录后应显示 Logged in as 用户名");

        // 5 登出模块：再次退出，验证账号会话被清除
        SignupLoginPage afterLogout = afterCorrectLogin.clickLogout();
        Assert.assertTrue(afterLogout.isLoginPageDisplayed(), "最终登出后应返回登录页");
    }
}
