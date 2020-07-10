# coding: utf-8

import apex
import os




def main(dict={}):
#def main():
	apex.disableShowOutput()

	myModel = apex.currentModel()
	
	matls = apex.catalog.getMaterials([{"path":myModel.getName()+"/Materials"}])
	
	matlNames = []
	for matl in matls:
		matlType = matl.getMaterialType()
		if matlType != 0: continue  # 0 is isotropic
		matlNames.append(matl.getName())
		if matl.getMaterialType() > 0: continue
		#print(matl.getElasticModulus())
		#print(matl.getDensity())
		#print(matl.getPoissonRatio())
		
	
	if len(matlNames) == 0: matlNames.append("None")
	
	ret_dict = {}
	ret_dict["matlList"] = matlNames
	
	return ret_dict
	


#main()


