"""System events — sleep/wake and app launches (macOS, via NSWorkspace)."""

import AppKit
import objc

from claudy.content.app_reactions import MACOS_APPS
from claudy.log import reported


class SystemEventObserver(AppKit.NSObject):
    """Subscribes to NSWorkspace notifications and feeds the controller."""

    def initWithController_(self, controller):
        self = objc.super(SystemEventObserver, self).init()
        if self is None:
            return None
        self.controller = controller
        nc = AppKit.NSWorkspace.sharedWorkspace().notificationCenter()
        nc.addObserver_selector_name_object_(
            self, "handleSleep:", AppKit.NSWorkspaceWillSleepNotification, None)
        nc.addObserver_selector_name_object_(
            self, "handleWake:", AppKit.NSWorkspaceDidWakeNotification, None)
        nc.addObserver_selector_name_object_(
            self, "handleAppLaunch:",
            AppKit.NSWorkspaceDidLaunchApplicationNotification, None)
        return self

    # AppKit swallows what a notification handler raises, so each runs its
    # body under reported() to get it into error.log

    def handleSleep_(self, notification):
        with reported("sleep"):
            self.controller.on_system_sleep()

    def handleWake_(self, notification):
        with reported("wake"):
            self.controller.on_system_wake()

    def handleAppLaunch_(self, notification):
        info = notification.userInfo()
        app_obj = info.get("NSWorkspaceApplicationKey") if info else None
        bundle_id = app_obj.bundleIdentifier() if app_obj else None
        if not bundle_id:
            return
        bundle_id = str(bundle_id)
        name = str(app_obj.localizedName() or "")
        with reported(f"reacting to {bundle_id}"):
            self.controller.on_app_launched(
                bundle_id, MACOS_APPS.get(bundle_id), name)
