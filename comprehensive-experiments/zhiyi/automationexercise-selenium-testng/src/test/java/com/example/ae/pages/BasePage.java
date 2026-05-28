package com.example.ae.pages;

import org.openqa.selenium.*;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public abstract class BasePage {
    protected final WebDriver driver;
    protected final WebDriverWait wait;

    protected BasePage(WebDriver driver, WebDriverWait wait) {
        this.driver = driver;
        this.wait = wait;
    }

    protected WebElement visible(By by) {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(by));
    }

    protected WebElement clickable(By by) {
        return wait.until(ExpectedConditions.elementToBeClickable(by));
    }

    protected void click(By by) {
        WebElement element = clickable(by);
        try {
            ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", element);
            element.click();
        } catch (ElementClickInterceptedException | StaleElementReferenceException e) {
            WebElement fresh = clickable(by);
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", fresh);
        } catch (TimeoutException e) {
            // 点击后页面跳转时，广告/外部脚本可能导致 renderer 超时。停止加载后交给后续显式等待处理。
            try {
                ((JavascriptExecutor) driver).executeScript("window.stop();");
            } catch (Exception ignored) {
            }
        }
    }

    protected void type(By by, String text) {
        WebElement element = visible(by);
        element.clear();
        if (text != null) {
            element.sendKeys(text);
        }
    }

    protected boolean isVisible(By by) {
        try {
            return driver.findElement(by).isDisplayed();
        } catch (NoSuchElementException | StaleElementReferenceException e) {
            return false;
        }
    }

    protected boolean isVisibleAfterWait(By by) {
        try {
            wait.until(ExpectedConditions.visibilityOfElementLocated(by));
            return true;
        } catch (TimeoutException e) {
            return false;
        }
    }
}
