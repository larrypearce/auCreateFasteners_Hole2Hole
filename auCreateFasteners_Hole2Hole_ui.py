import sys
import os
import apex_sdk
import clr

#.NET references
import System
import System.Windows.Controls as WPFControls
from System.Windows.Automation import AutomationProperties
from Microsoft.Win32 import OpenFileDialog



#setting pre-defined properties of tool_propertyContainer
def getUIContent():
	my_toolProperty = apex_sdk.ToolPropertyContainer()
	
	my_toolProperty.TitleText = "AuFast 1.6"
	
	file_path = os.path.dirname(os.path.realpath(__file__))
	#my_toolProperty.TitleImageUriString = os.path.join(os.path.dirname(file_path), r'..\\icons\\auFast.png')
	my_toolProperty.TitleImageUriString = file_path+"./auFast.png"
	
	
	my_toolProperty.WorkFlowInstructions = """<HTML><BODY><P STYLE=\"font-size:10;\"><SPAN>AuFast 1.4</SPAN></P>
	<P><SPAN> </SPAN></P>
	<P><SPAN>This script creates hole-to-hole fastener connections for surface-to-surface, surface-to-solid, and solid-to-solid connections.</SPAN></P>
	<P STYLE=\"font-size:10;\"><SPAN>Send questions, comments and Elvis sightings to larry.pearce@mscsoftware.com</SPAN></P></BODY></HTML>"""

	
	
	#handle apply button (green) click event
	my_toolProperty.AppliedCommand = apex_sdk.ActionCommand(System.Action(HandleApplyButton))
	# handle exit button (red) click event
	my_toolProperty.ExitCommand = apex_sdk.ActionCommand(System.Action(HandleExitButton))
	
	my_toolProperty.ToolPropertyContent = getCustomToolPropertyContent()
	
	#define pickFiterTools
	my_toolProperty.ShowPickChoice = True
	my_toolProperty.IsCustomTool   = True
	#setPickFilterTools()
	my_toolProperty.PickFilterList = setPickFilterTools()
	
	return my_toolProperty





def getCustomToolPropertyContent():

	my_Grid = WPFControls.Grid()

	nRows = 8
	nCols = 2
	createLayout(my_Grid, nRows, nCols)
	iRow = iCol = 0
	
	global nameTextBox
	nameTextBox = createDataBox(my_Grid, "Name: ", "", iRow, iCol)
	iRow += 1
	
	global fastenerTypeComboBox
	fastenerTypeComboBox = createComboBox2(my_Grid, "Fastener Type:", ["Flexible", "Bushing", "Rigid"], 0, iRow, iCol)
	iRow += 1
	
	global distributionTypeComboBox
	distributionTypeComboBox = createComboBox2(my_Grid, "Distribution:", ["Compliant", "Rigid"], 0, iRow, iCol)
	iRow += 1
	
	global materialComboBox
	global matlComboTextBox
	matlComboTextBlock = createTextBlock(my_Grid, "Material:", iRow, 0)
	materialComboBox   = createComboBox(my_Grid, iRow, 1)
	iRow += 1
	
	file_path = os.path.dirname(os.path.realpath(__file__))
	script_path= os.path.join(file_path, 'auGetMaterials.py')
	apex_sdk.runScriptFunction(script_path, "main", callback=getMatls)
	
	global toleranceTextBox
	toleranceTextBox = createDataBox(my_Grid, "Tolerance:", "0.1", iRow, iCol)
	iRow += 1
	
	global maxDiameterTextBox
	maxDiameterTextBox = createDataBox(my_Grid, "Max Diameter:", "0.75", iRow, iCol)
	iRow += 1
	
	global attachWasherToggle, washerFactorTextBlock, washerFactorTextBox
	
	attachWasherToggle =  createCheckBox(my_Grid, "Attach Shell Mesh Washer", iRow, 0)
	iRow += 1
	
	attachWasherToggle.Checked   += attachWasherHandleCheck
	attachWasherToggle.Unchecked += attachWasherHandleUnCheck
	
	washerFactorTextBlock = createTextBlock(my_Grid, "Washer Factor (>1.0):", iRow, 0)
	washerFactorTextBox   = createTextBox(my_Grid,   "1.2",              iRow, 1)
	iRow += 1
	
	washerFactorTextBlock.Visibility = System.Windows.Visibility.Collapsed
	washerFactorTextBox.Visibility = System.Windows.Visibility.Collapsed
	
	
	
	return my_Grid




def attachWasherHandleCheck(sender, event):
	global washerFactorTextBlock, washerFactorTextBox
	
	washerFactorTextBlock.Visibility = System.Windows.Visibility.Visible
	washerFactorTextBox.Visibility = System.Windows.Visibility.Visible

def attachWasherHandleUnCheck(sender, event):
	global washerFactorTextBlock, washerFactorTextBox
	
	washerFactorTextBlock.Visibility = System.Windows.Visibility.Collapsed
	washerFactorTextBox.Visibility = System.Windows.Visibility.Collapsed




def createCheckBox(parent, label, row, col):

	checkBox = WPFControls.CheckBox()
	checkBox.Content = label
	checkBox.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(checkBox, row)
	WPFControls.Grid.SetColumn(checkBox, col)
	
	parent.Children.Add(checkBox)
	
	return checkBox



def createLayout(parent, numRows, numCols):
	for k in range(numRows):
		parent.RowDefinitions.Add(WPFControls.RowDefinition())
	for k in range(numCols):
		parent.ColumnDefinitions.Add(WPFControls.ColumnDefinition())




def createComboBox(parent, row, col):
	comboBox = WPFControls.ComboBox()
	
	comboBox.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(comboBox, row)
	WPFControls.Grid.SetColumn(comboBox, col)
	
	parent.Children.Add(comboBox)
	
	return comboBox



def updateComboBox(comboBox, comboItems):
	
	for comboItem in comboItems:
		item = WPFControls.ComboBoxItem()
		item.Content=comboItem
		comboBox.Items.Add(item)
	
	comboBox.SelectedIndex="0"



def createTextBlock(parent, text, row, col):
	textBlock = WPFControls.TextBlock()
	textBlock.Text = text
	
	textBlock.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBlock, row)
	WPFControls.Grid.SetColumn(textBlock, col)
	parent.Children.Add(textBlock)
	
	return textBlock



def createTextBlock2(parent, text, row, col):
	textBlock = WPFControls.TextBlock()
	textBlock.Text = text
	
	textBlock.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBlock, row)
	WPFControls.Grid.SetColumn(textBlock, col)
	parent.Children.Add(textBlock)
	
	return textBlock



def createTextBox(parent, value, row, col):
	textBox =WPFControls.TextBox()
	
	textBox.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBox, row)
	WPFControls.Grid.SetColumn(textBox, col)
	textBox.Text=value
	
	parent.Children.Add(textBox)
	
	return textBox




def createComboBox2(parent, title, labels, selected, row, col):
	textBlock = WPFControls.TextBlock()
	textBlock.Text = title
	
	textBlock.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBlock, row)
	WPFControls.Grid.SetColumn(textBlock, col)

	parent.Children.Add(textBlock)
	
	comboBox = WPFControls.ComboBox()
	
	comboBox.Margin = System.Windows.Thickness(5.)
	
	for label in labels:
		item = WPFControls.ComboBoxItem()
		item.Content=label
		comboBox.Items.Add(item)
	
	WPFControls.Grid.SetRow(comboBox, row)
	WPFControls.Grid.SetColumn(comboBox, col+1)
	
	if selected > len(labels): selected = 0
	comboBox.SelectedIndex=str(selected)
	
	parent.Children.Add(comboBox)
	
	return comboBox






def createDataBox(parent, title, value, row, col):
	textBlock = WPFControls.TextBlock()
	textBlock.Text = title
	
	textBlock.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBlock, row)
	WPFControls.Grid.SetColumn(textBlock, col)

	textBox =WPFControls.TextBox()
	
	textBox.Margin = System.Windows.Thickness(5.)
	
	WPFControls.Grid.SetRow(textBox, row)
	WPFControls.Grid.SetColumn(textBox, col+1)
	textBox.Text=value
	
	parent.Children.Add(textBlock)
	parent.Children.Add(textBox)
	
	return textBox






#set pickFilers
#some pick choices are commented out
def setPickFilterTools():
	pickChoices = System.Collections.Generic.List[System.String]()
	
	#exclusive picking and visibility picking	
	pickChoices.Add(apex_sdk.PickFilterTypes.ExclusivePicking)
	pickChoices.Add(apex_sdk.PickFilterTypes.VisibilityPicking)
	
	#Assembly and part
	#pickChoices.Add(apex_sdk.PickFilterTypes.Assembly)
	pickChoices.Add(apex_sdk.PickFilterTypes.Part)
	
	#Bodies	
	#pickChoices.Add(apex_sdk.PickFilterTypes.SolidMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Solid)
	#pickChoices.Add(apex_sdk.PickFilterTypes.SurfaceMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Surface)
	#pickChoices.Add(apex_sdk.PickFilterTypes.CurveMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Curve)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Point)
	
	#features
	#pickChoices.Add(apex_sdk.PickFilterTypes.CellMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.FaceMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.EdgeMesh)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Cell)
	#pickChoices.Add(apex_sdk.PickFilterTypes.VertexMesh)
	
	#Lower Dimensional Entities
	#pickChoices.Add(apex_sdk.PickFilterTypes.Element3D)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Element2D)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Face)
	#pickChoices.Add(apex_sdk.PickFilterTypes.MeshSeed)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Element1D)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Edge)
	#pickChoices.Add(apex_sdk.PickFilterTypes.SeedPoint)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Node)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Vertex)
	
	#Sub Lower Dimensional Entities
	#pickChoices.Add(apex_sdk.PickFilterTypes.ElementEdge)
	#pickChoices.Add(apex_sdk.PickFilterTypes.ElementFace)
	
	#Interactions and connections
	#pickChoices.Add(apex_sdk.PickFilterTypes.DiscreteTie)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Connector)
	#pickChoices.Add(apex_sdk.PickFilterTypes.EdgeTie)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Joint)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Glue)
	
	#LBCs
	#pickChoices.Add(apex_sdk.PickFilterTypes.Pressure)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Gravity)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Constraint)
	#pickChoices.Add(apex_sdk.PickFilterTypes.ForceMoment)
	#pickChoices.Add(apex_sdk.PickFilterTypes.EnforcedMotion)
	
	#Attributes and other objects
	#pickChoices.Add(apex_sdk.PickFilterTypes.CompositeZone)
	#pickChoices.Add(apex_sdk.PickFilterTypes.LayeredPanel)
	#pickChoices.Add(apex_sdk.PickFilterTypes.InterfacePoint)
	#pickChoices.Add(apex_sdk.PickFilterTypes.PointMass)
	#pickChoices.Add(apex_sdk.PickFilterTypes.BeamSpan)
	#pickChoices.Add(apex_sdk.PickFilterTypes.Offset)
	
	#Sensors
	#pickChoices.Add(apex_sdk.PickFilterTypes.MotionEnvelopeSensor)
	#pickChoices.Add(apex_sdk.PickFilterTypes.ClearanceSensor)
	#pickChoices.Add(apex_sdk.PickFilterTypes.CrossSectionSensor)
	#pickChoices.Add(apex_sdk.PickFilterTypes.PointSensor)
	
	#Coordinate system
	#pickChoices.Add(apex_sdk.PickFilterTypes.CoordinateSystem)
	
	#Tool Registration
	#Tool Name has to be the same
	#apex_sdk.PickFilterRegistration.RegisterTool("Auto Tie Nodes", pickChoices)
	return pickChoices






@apex_sdk.errorhandler
def HandleApplyButton():
	# Create a Dictionary to store the user defined tool data  
	dictionary = {}
	
	choices = materialComboBox.SelectedValue.ToString().split(":")
	material = choices[len(choices)-1].lstrip().rstrip()
	
	choices = fastenerTypeComboBox.SelectedValue.ToString().split(":")
	fastenerType = choices[len(choices)-1].lstrip().rstrip()
	
	choices = distributionTypeComboBox.SelectedValue.ToString().split(":")
	distributionType = choices[len(choices)-1].lstrip().rstrip()
	
	dictionary["attachWasher"] = attachWasherToggle.IsChecked
	
	dictionary["washerFactor"] = washerFactorTextBox.Text
	
	dictionary["name"]             = nameTextBox.Text
	dictionary["material"]         = material
	dictionary["fastenerType"]     = fastenerType
	dictionary["distributionType"] = distributionType
	dictionary["tolerance"]        = toleranceTextBox.Text
	dictionary["maxDiameter"]      = maxDiameterTextBox.Text
	
	
	file_path = os.path.dirname(os.path.realpath(__file__))
	script_path= os.path.join(file_path, 'auCreateFasteners_Hole2Hole_3a.py')
	
	apex_sdk.runScriptFunction(script_path, "main", dictionary)
	
	
	
	
	
	
# exit button (red) from tool header
@apex_sdk.errorhandler
def HandleExitButton():
	print("HandleExitButton")






#This function receives data from the Script API function and updates the Tool UI 
@apex_sdk.errorhandler
def getMatls():
	global matlComboBox
	
	ret_dict = apex_sdk.getScriptFunctionReturnData()
	
	matls = ret_dict["matlList"]
	
	updateComboBox(materialComboBox, matls)
