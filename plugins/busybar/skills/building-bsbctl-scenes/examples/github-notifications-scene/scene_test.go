package githubnotificationscene

import (
	"image"
	_ "image/png"
	"os"
	"reflect"
	"strings"
	"testing"

	"github.com/lxdb/bsbctl/sdk/protocol"
)

func TestStatesPreserveCompleteMessagesAndStableFrontLayout(t *testing.T) {
	tests := []struct {
		view     View
		headline string
		context  string
		color    string
	}{
		{View{Kind: KindReviewRequested, Subject: "GitHub Notifications release", Repository: "lxdb/bsbctl"}, "Review requested: GitHub Notifications release", "lxdb/bsbctl", reviewColor},
		{View{Kind: KindMentioned, Subject: "Can you review the release change?", Repository: "lxdb/bsbctl"}, "Mentioned: Can you review the release change?", "lxdb/bsbctl", mentionColor},
		{View{Kind: KindNoUnread}, "No unread GitHub notifications", "Source is current", primaryColor},
		{View{Kind: KindSetupRequired}, "GitHub setup required", "Run bsbctl app setup", reviewColor},
		{View{Kind: KindConnectionFailed}, "GitHub connection failed", "Check token and network", failureColor},
	}

	var topology []protocol.Element
	for _, test := range tests {
		scene, err := Build(test.view)
		if err != nil {
			t.Fatal(err)
		}
		if err := scene.Validate(); err != nil {
			t.Fatal(err)
		}
		elements := byID(scene.Elements)
		headline := elements["front-headline"]
		context := elements["front-context"]
		icon := elements["front-icon"]
		if headline.Text.Value != test.headline || headline.Text.Color != test.color || headline.X != 18 || headline.Y != 0 || headline.Text.Width != 54 || headline.Text.Marquee == nil {
			t.Fatalf("headline for %s: %+v", test.view.Kind, headline)
		}
		if context.Text.Value != test.context || context.X != 18 || context.Y != 9 || context.Text.Width != 54 || context.Text.Marquee == nil {
			t.Fatalf("context for %s: %+v", test.view.Kind, context)
		}
		if icon.X != 0 || icon.Y != 0 || icon.Image == nil || icon.Image.Asset.PackagePath != "assets/github-mark.png" {
			t.Fatalf("icon for %s: %+v", test.view.Kind, icon)
		}
		for _, privateCode := range []string{"SLK", "NTFN", "NTION", "AUTH"} {
			if strings.Contains(headline.Text.Value, privateCode) || strings.Contains(context.Text.Value, privateCode) {
				t.Fatalf("%s uses private code %q", test.view.Kind, privateCode)
			}
		}
		shape := elementShape(scene.Elements)
		if topology == nil {
			topology = shape
		} else if !reflect.DeepEqual(shape, topology) {
			t.Fatalf("%s changed element topology", test.view.Kind)
		}
	}
}

func TestBundledGitHubMarkIsNativeSize(t *testing.T) {
	file, err := os.Open("assets/github-mark.png")
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	config, _, err := image.DecodeConfig(file)
	if err != nil {
		t.Fatal(err)
	}
	if config.Width != 16 || config.Height != 16 {
		t.Fatalf("GitHub mark is %dx%d, want 16x16", config.Width, config.Height)
	}
}

func TestInvalidSemanticInputsFail(t *testing.T) {
	for _, view := range []View{
		{Kind: KindReviewRequested, Repository: "lxdb/bsbctl"},
		{Kind: KindMentioned, Subject: "Review this"},
		{Kind: "unknown"},
		{Kind: KindReviewRequested, Subject: strings.Repeat("x", protocol.MaxTextBytes), Repository: "lxdb/bsbctl"},
	} {
		if _, err := Build(view); err == nil {
			t.Fatalf("Build(%+v) succeeded", view)
		}
	}
}

func byID(elements []protocol.Element) map[string]protocol.Element {
	result := make(map[string]protocol.Element, len(elements))
	for _, element := range elements {
		result[element.ID] = element
	}
	return result
}

func elementShape(elements []protocol.Element) []protocol.Element {
	result := make([]protocol.Element, 0, len(elements))
	for _, element := range elements {
		result = append(result, protocol.Element{
			ID: element.ID, Display: element.Display, X: element.X, Y: element.Y,
			Rectangle: shapeRectangle(element.Rectangle), Text: shapeText(element.Text), Image: shapeImage(element.Image),
		})
	}
	return result
}

func shapeRectangle(value *protocol.RectangleElement) *protocol.RectangleElement {
	if value == nil {
		return nil
	}
	return &protocol.RectangleElement{Width: value.Width, Height: value.Height}
}

func shapeText(value *protocol.TextElement) *protocol.TextElement {
	if value == nil {
		return nil
	}
	return &protocol.TextElement{Font: value.Font, Width: value.Width}
}

func shapeImage(value *protocol.ImageElement) *protocol.ImageElement {
	if value == nil {
		return nil
	}
	return &protocol.ImageElement{Asset: value.Asset}
}
