// Package githubnotificationscene demonstrates a product-branded notification scene.
package githubnotificationscene

import (
	"errors"
	"fmt"

	"github.com/lxdb/bsbctl/sdk/protocol"
)

const (
	KindReviewRequested  = "review_requested"
	KindMentioned        = "mentioned"
	KindNoUnread         = "no_unread"
	KindSetupRequired    = "setup_required"
	KindConnectionFailed = "connection_failed"

	canvasColor    = "#0D1117FF"
	primaryColor   = "#F0F6FCFF"
	secondaryColor = "#8B949EFF"
	mentionColor   = "#58A6FFFF"
	reviewColor    = "#D29922FF"
	failureColor   = "#F85149FF"
)

// View is the semantic input to the scene. Subject and Repository are required
// only for notification states.
type View struct {
	Kind       string
	Subject    string
	Repository string
}

type copySet struct {
	headline string
	context  string
	color    string
	back     [4]string
}

// Build translates a notification state into stable front and back elements.
func Build(view View) (protocol.Scene, error) {
	content, err := copyFor(view)
	if err != nil {
		return protocol.Scene{}, err
	}
	for _, value := range append([]string{content.headline, content.context}, content.back[:]...) {
		if len([]byte(value)) > protocol.MaxTextBytes {
			return protocol.Scene{}, fmt.Errorf("text exceeds %d bytes", protocol.MaxTextBytes)
		}
	}

	marquee := func(value, font, color string, width int) *protocol.TextElement {
		return &protocol.TextElement{
			Value: value,
			Font:  font,
			Color: color,
			Width: width,
			Marquee: &protocol.Marquee{
				PixelsPerMinute:         1000,
				StartDelayMilliseconds:  1000,
				RepeatDelayMilliseconds: 2500,
			},
		}
	}

	elements := []protocol.Element{
		{ID: "front-background", Display: protocol.DisplayFront, Rectangle: &protocol.RectangleElement{Width: 72, Height: 16, Color: canvasColor}},
		{ID: "front-headline", Display: protocol.DisplayFront, X: 18, Y: 0, Text: marquee(content.headline, "normal", content.color, 54)},
		{ID: "front-context", Display: protocol.DisplayFront, X: 18, Y: 9, Text: marquee(content.context, "tiny", secondaryColor, 54)},
		{ID: "front-icon", Display: protocol.DisplayFront, Image: &protocol.ImageElement{Asset: protocol.AssetRef{PackagePath: "assets/github-mark.png"}}},
		{ID: "back-background", Display: protocol.DisplayBack, Rectangle: &protocol.RectangleElement{Width: 160, Height: 80, Color: canvasColor}},
	}
	for index, value := range content.back {
		elements = append(elements, protocol.Element{
			ID:      fmt.Sprintf("back-line-%d", index),
			Display: protocol.DisplayBack,
			X:       4,
			Y:       4 + index*14,
			Text:    marquee(value, "small", primaryColor, 152),
		})
	}
	scene := protocol.Scene{Elements: elements}
	if err := scene.Validate(); err != nil {
		return protocol.Scene{}, fmt.Errorf("validate scene: %w", err)
	}
	return scene, nil
}

func copyFor(view View) (copySet, error) {
	switch view.Kind {
	case KindReviewRequested:
		if view.Subject == "" || view.Repository == "" {
			return copySet{}, errors.New("review request requires subject and repository")
		}
		return copySet{
			headline: "Review requested: " + view.Subject,
			context:  view.Repository,
			color:    reviewColor,
			back:     [4]string{"GitHub Notifications", "Review requested", view.Repository + " / " + view.Subject, "START: OPEN AND MARK READ"},
		}, nil
	case KindMentioned:
		if view.Subject == "" || view.Repository == "" {
			return copySet{}, errors.New("mention requires subject and repository")
		}
		return copySet{
			headline: "Mentioned: " + view.Subject,
			context:  view.Repository,
			color:    mentionColor,
			back:     [4]string{"GitHub Notifications", "Mentioned", view.Repository + " / " + view.Subject, "START: OPEN AND MARK READ"},
		}, nil
	case KindNoUnread:
		return copySet{
			headline: "No unread GitHub notifications",
			context:  "Source is current",
			color:    primaryColor,
			back:     [4]string{"GitHub Notifications", "No unread notifications", "Source is current", "BACK: CLOSE"},
		}, nil
	case KindSetupRequired:
		return copySet{
			headline: "GitHub setup required",
			context:  "Run bsbctl app setup",
			color:    reviewColor,
			back:     [4]string{"GitHub Notifications", "Setup required", "Add a token with notification access", "BACK: CLOSE"},
		}, nil
	case KindConnectionFailed:
		return copySet{
			headline: "GitHub connection failed",
			context:  "Check token and network",
			color:    failureColor,
			back:     [4]string{"GitHub Notifications", "Connection failed", "Check token and network", "BACK: CLOSE"},
		}, nil
	default:
		return copySet{}, fmt.Errorf("unsupported notification kind %q", view.Kind)
	}
}
