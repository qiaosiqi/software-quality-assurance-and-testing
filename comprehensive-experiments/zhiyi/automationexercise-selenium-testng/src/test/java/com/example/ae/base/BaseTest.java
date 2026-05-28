package com.example.ae.base;

import com.example.ae.pages.HomePage;
import com.example.ae.utils.Config;
import org.openqa.selenium.*;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.ITestContext;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;

import java.time.Duration;

/**
 * 所有 Selenium 测试的公共父类。
 */
public abstract class BaseTest {
    protected WebDriver driver;
    protected WebDriverWait wait;
    protected String baseUrl;
    protected String browser;
    protected boolean headless;
    protected int timeoutSeconds;
    protected String defaultUserName;
    protected String defaultPassword;
    protected String emailDomain;

    @BeforeMethod(alwaysRun = true)
    public void setUp(ITestContext context) {
        baseUrl = Config.normalizeBaseUrl(Config.get(context, "baseUrl", "https://automationexercise.com"));
        browser = Config.get(context, "browser", "chrome");
        headless = Config.getBoolean(context, "headless", false);
        timeoutSeconds = Config.getInt(context, "timeoutSeconds", 18);
        defaultUserName = Config.get(context, "username", "Selenium Student");
        defaultPassword = Config.get(context, "password", "Test@123456");
        emailDomain = Config.get(context, "emailDomain", "example.com");

        driver = BrowserFactory.createDriver(browser, headless);
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(0));
        driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(Math.max(timeoutSeconds, 45)));
        driver.manage().window().maximize();
        wait = new WebDriverWait(driver, Duration.ofSeconds(timeoutSeconds));
    }

    @AfterMethod(alwaysRun = true)
    public void tearDown() {
        if (driver != null) {
            try {
                driver.quit();
            } catch (WebDriverException ignored) {
            }
        }
    }

    protected void openHome() {
        safeOpen(baseUrl + "/");
        closeGoogleVignetteIfPresent();
        new HomePage(driver, wait).waitUntilLoaded();
    }

    protected void openLogin() {
        safeOpen(baseUrl + "/login");
        closeGoogleVignetteIfPresent();
        new com.example.ae.pages.SignupLoginPage(driver, wait).waitUntilLoaded();
    }

    /**
     * 目标网站有大量广告和外部脚本，普通 driver.get() 偶尔会一直等资源加载。
     * 这里采用“超时后停止加载 + 继续等待主体元素”的方式，提高实验运行稳定性。
     */
    protected void safeOpen(String url) {
        try {
            driver.get(url);
        } catch (TimeoutException e) {
            stopLoading();
        }
        waitForPageReady();
    }

    protected void stopLoading() {
        try {
            ((JavascriptExecutor) driver).executeScript("window.stop();");
        } catch (Exception ignored) {
        }
    }

    protected void waitForPageReady() {
        wait.until((ExpectedCondition<Boolean>) d -> {
            Object result = ((JavascriptExecutor) d).executeScript("return document.readyState");
            return "complete".equals(result) || "interactive".equals(result);
        });
    }

    /**
     * automationexercise.com 偶尔会出现广告遮挡；该方法只做兼容，不影响正常页面。
     */
    protected void closeGoogleVignetteIfPresent() {
        try {
            driver.switchTo().defaultContent();
            for (WebElement iframe : driver.findElements(By.cssSelector("iframe"))) {
                try {
                    String title = iframe.getAttribute("title");
                    String name = iframe.getAttribute("name");
                    if ((title != null && title.toLowerCase().contains("advertisement"))
                            || (name != null && name.toLowerCase().contains("google"))) {
                        driver.switchTo().frame(iframe);
                        for (WebElement close : driver.findElements(By.cssSelector("[aria-label='Close'], [aria-label='关闭'], #dismiss-button"))) {
                            if (close.isDisplayed()) {
                                close.click();
                                break;
                            }
                        }
                        driver.switchTo().defaultContent();
                    }
                } catch (Exception ignored) {
                    driver.switchTo().defaultContent();
                }
            }
        } catch (Exception ignored) {
            driver.switchTo().defaultContent();
        }
    }

    protected boolean hasHtml5ValidationMessage(WebElement element) {
        Object msg = ((JavascriptExecutor) driver).executeScript("return arguments[0].validationMessage;", element);
        return msg != null && !String.valueOf(msg).isBlank();
    }
}
